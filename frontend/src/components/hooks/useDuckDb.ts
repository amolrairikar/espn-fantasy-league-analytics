import * as duckdb from '@duckdb/duckdb-wasm';
import { useState, useEffect } from 'react';

import duckdb_wasm from '@duckdb/duckdb-wasm/dist/duckdb-mvp.wasm?url';
import mvp_worker from '@duckdb/duckdb-wasm/dist/duckdb-browser-mvp.worker.js?url';
import duckdb_wasm_eh from '@duckdb/duckdb-wasm/dist/duckdb-eh.wasm?url';
import eh_worker from '@duckdb/duckdb-wasm/dist/duckdb-browser-eh.worker.js?url';

// Define the manual bundle mapping
const MANUAL_BUNDLES: duckdb.DuckDBBundles = {
    mvp: {
        mainModule: duckdb_wasm,
        mainWorker: mvp_worker,
    },
    eh: {
        mainModule: duckdb_wasm_eh,
        mainWorker: eh_worker,
    },
};

interface DuckDBState {
    db: duckdb.AsyncDuckDB | null;
    loading: boolean;
    error: Error | null;
}

export const useDuckDB = (): DuckDBState => {
    const [db, setDb] = useState<duckdb.AsyncDuckDB | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        let isMounted = true;
        let worker: Worker | null = null;
        let dbInstance: duckdb.AsyncDuckDB | null = null;

        const init = async () => {
            try {
                // Select the best bundle from our local assets
                const BUNDLE = await duckdb.selectBundle(MANUAL_BUNDLES);

                // Initialize the worker using the local URL
                worker = new Worker(BUNDLE.mainWorker!);
                const logger = new duckdb.ConsoleLogger();
                dbInstance = new duckdb.AsyncDuckDB(logger, worker);

                // Instantiate the WASM module
                await dbInstance.instantiate(BUNDLE.mainModule, BUNDLE.pthreadWorker);

                // Do not call db.open() here — ensureLatestDatabase will register
                // the database buffer and open it after downloading from S3, so
                // the engine never holds a file lock before the sync writes.
                if (isMounted) {
                    setDb(dbInstance);
                    setLoading(false);
                }
            } catch (err) {
                console.error("DuckDB Init Error:", err);
                if (isMounted) {
                    setError(err instanceof Error ? err : new Error('Failed to init DuckDB'));
                    setLoading(false);
                }
            }
        };

        init();

        return () => {
            isMounted = false;
            // Terminate the engine on cleanup so StrictMode's double-invocation
            // doesn't leave an orphaned worker running in the background
            if (dbInstance) {
                dbInstance.terminate();
            } else if (worker) {
                worker.terminate();
            }
        };
    }, []);

    return { db, loading, error };
};