import * as duckdb from '@duckdb/duckdb-wasm';

/**
 * Executes a SQL query against the given DuckDB instance.
 * Sync is handled upstream (Home.tsx → ensureLatestDatabase) before queries run.
 * Use the generic <T> to define the expected shape of a single row.
 * @param db - The DuckDB instance.
 * @param sql - The SQL query to run.
 * @returns {Promise<T[]>} - The result rows as an array of typed objects.
 */
export const executeQuery = async <T = any>(
    db: duckdb.AsyncDuckDB | null,
    sql: string
): Promise<T[]> => {

    if (!db) {
        throw new Error("DuckDB not initialized");
    }

    const conn = await db.connect();
    
    try {
        const result = await conn.query(sql);
        
        // Convert Arrow Table to plain JS objects and handle BigInts immediately
        return result.toArray().map((row) => {
            const obj = row.toJSON();
            for (const key in obj) {
                if (typeof obj[key] === 'bigint') {
                    obj[key] = Number(obj[key]);
                }
            }
            return obj as T;
        });
    } catch (error) {
        console.error("DuckDB Query Error:", error);
        throw error;
    } finally {
        await conn.close();
    }
};