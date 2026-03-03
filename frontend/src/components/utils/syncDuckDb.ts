import * as duckdb from '@duckdb/duckdb-wasm';
import { getLeagueDatabase } from '@/api/database/api_calls';

interface DBMetadata {
    url: string;
    version: string;
    size: number;
}

const OPFS_PATH = 'opfs/main.db';

/**
 * Ensures the local OPFS database is up to date with S3.
 * @param {AsyncDuckDB} db - The initialized DuckDB instance
 */
export const ensureLatestDatabase = async (db: duckdb.AsyncDuckDB): Promise<boolean> => {
    const leagueId = localStorage.getItem('league_id')

    // Get current version info from FastAPI
    const resp = await getLeagueDatabase(leagueId!);
    if (!resp.data) {
        throw new Error("Failed to fetch DB metadata");
    }
    
    const { url, version, size }: DBMetadata = resp.data;
    const localVersion = localStorage.getItem('db_version');

    // If versions mismatch, download and overwrite
    if (localVersion !== version) {
        console.log(`Syncing DB: Local(${localVersion}) -> Remote(${version})`);
        
        const fileResp = await fetch(url);
        if (!fileResp.ok) {
            throw new Error("Failed to download DB file from S3");
        }
        
        const buffer = await fileResp.arrayBuffer();
        const uint8Array = new Uint8Array(buffer);
        
        await db.dropFile(OPFS_PATH); // Clear any existing handle
        await db.registerFileBuffer(OPFS_PATH, uint8Array);
        
        // Re-open to ensure the engine points to the new buffer
        await db.open({ 
            path: OPFS_PATH,
            accessMode: duckdb.DuckDBAccessMode.READ_WRITE 
        });
    }

    return true;
};
