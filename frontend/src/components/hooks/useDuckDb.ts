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

        const init = async () => {
            try {
                // Select the best bundle from our local assets
                const BUNDLE = await duckdb.selectBundle(MANUAL_BUNDLES);
                
                // Initialize the worker using the local URL
                const worker = new Worker(BUNDLE.mainWorker!);
                const logger = new duckdb.ConsoleLogger();
                const dbInstance = new duckdb.AsyncDuckDB(logger, worker);
                
                // Instantiate the WASM module
                await dbInstance.instantiate(BUNDLE.mainModule, BUNDLE.pthreadWorker);
                
                // Open DuckDB using the Origin Private File System (OPFS) path
                await dbInstance.open({ 
                    path: 'opfs/main.db', 
                    accessMode: duckdb.DuckDBAccessMode.READ_WRITE // Explicitly allow writing/creation
                });
                
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
        };
    }, []);

    return { db, loading, error };
};