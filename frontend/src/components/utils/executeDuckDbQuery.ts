import * as duckdb from '@duckdb/duckdb-wasm';
import { ensureLatestDatabase } from '@/components/utils/syncDuckDb';

/**
 * Higher-order function to execute a query with auto-sync.
 * Use the generic <T> to define the expected shape of a single row.
 * * @param db - The DuckDB instance.
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

    await ensureLatestDatabase(db);
    const conn = await db.connect();
    
    try {
        const result = await conn.query(sql);
        
        // result.toArray() returns Arrow Rows. 
        // .toJSON() converts the Arrow Map-like object into a plain JS object.
        return result.toArray().map((row) => row.toJSON() as T);
    } catch (error) {
        console.error("DuckDB Query Error:", error);
        throw error;
    } finally {
        await conn.close();
    }
};