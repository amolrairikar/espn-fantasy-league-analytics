import * as duckdb from '@duckdb/duckdb-wasm';
import { getLeagueDatabase } from '@/api/database/api_calls';
import { cacheManager } from '@/components/utils/dbCacheManager';

/**
 * Ensures the local DuckDB instance has the latest database from S3.
 * Uses IndexedDB to cache the database bytes so page refreshes don't
 * re-download unless the S3 version (ETag) changes.
 *
 * Call this before running any queries. It handles both the first open
 * and re-opens on version change.
 *
 * @param db - The instantiated (but not yet opened) DuckDB engine
 */
export const ensureLatestDatabase = async (db: duckdb.AsyncDuckDB): Promise<boolean> => {
    const leagueId = localStorage.getItem('league_id');
    const resp = await getLeagueDatabase(leagueId!);
    
    if (!resp.data) throw new Error('Failed to fetch DB metadata');
    const { url, version } = resp.data;

    // Use the manager
    let buffer = await cacheManager.get(version);

    if (!buffer) {
        console.log(`DB cache miss (${version}), downloading...`);
        const fileResp = await fetch(url);
        if (!fileResp.ok) throw new Error('Download failed');
        
        buffer = new Uint8Array(await fileResp.arrayBuffer());
        await cacheManager.set(version, buffer);
    }

    await db.registerFileBuffer('main.db', buffer);
    await db.open({
        path: 'main.db',
        accessMode: duckdb.DuckDBAccessMode.READ_WRITE,
    });

    return true;
};
