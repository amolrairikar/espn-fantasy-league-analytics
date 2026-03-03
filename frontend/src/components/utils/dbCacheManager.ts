/**
 * Manages the persistence and retrieval of DuckDB binary buffers 
 * using IndexedDB as a client-side cache.
 */
class DatabaseCacheManager {
    private readonly dbName: string = 'fantasy-duckdb';
    private readonly storeName: string = 'db-cache';
    private readonly version: number = 1;

    /**
     * Internal helper to open the IndexedDB connection.
     * Ensures the object store exists before proceeding.
     */
    private async open(): Promise<IDBDatabase> {
        return new Promise((resolve, reject) => {
            const req = indexedDB.open(this.dbName, this.version);
            req.onupgradeneeded = () => {
                if (!req.result.objectStoreNames.contains(this.storeName)) {
                    req.result.createObjectStore(this.storeName);
                }
            };
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
        });
    }

    /**
     * Retrieves the cached database buffer if the version matches.
     * @param version - The unique identifier (ETag) for the requested DB.
     * @returns The buffer as a Uint8Array, or null if not found.
     */
    public async get(version: string): Promise<Uint8Array | null> {
        try {
            const idb = await this.open();
            return await new Promise((resolve) => {
                const tx = idb.transaction(this.storeName, 'readonly');
                const req = tx.objectStore(this.storeName).get(version);
                req.onsuccess = () => resolve(req.result ?? null);
                req.onerror = () => resolve(null);
            });
        } catch (err) {
            console.error('Cache read error:', err);
            return null;
        }
    }

    /**
     * Saves a new database buffer and evicts all previous versions.
     * This ensures the browser only ever stores one version of the DB at a time.
     * @param version - The new version identifier.
     * @param data - The raw DuckDB binary data.
     */
    public async set(version: string, data: Uint8Array): Promise<void> {
        try {
            const idb = await this.open();
            await new Promise<void>((resolve, reject) => {
                const tx = idb.transaction(this.storeName, 'readwrite');
                const store = tx.objectStore(this.storeName);

                // 1. Store new data
                store.put(data, version);

                // 2. Immediate Eviction Logic: Keep only the current version
                const keyReq = store.getAllKeys();
                keyReq.onsuccess = () => {
                    for (const key of keyReq.result) {
                        if (key !== version) store.delete(key);
                    }
                };

                tx.oncomplete = () => resolve();
                tx.onerror = () => reject(tx.error);
            });
        } catch (err) {
            // Non-fatal: the app still has the buffer in RAM from the fetch
            console.warn('Cache write failed. Persistence not available for this session.', err);
        }
    }
}

export const cacheManager = new DatabaseCacheManager();
