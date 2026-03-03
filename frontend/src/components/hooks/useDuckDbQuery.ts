import { useEffect, useState } from "react";
import * as duckdb from '@duckdb/duckdb-wasm';
import { executeQuery } from "@/components/utils/executeDuckDbQuery";


export function useDuckDbQuery<T>(db: duckdb.AsyncDuckDB | null, sql: string) {
  const [data, setData] = useState<T[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function run() {
      if (!db || !sql) return;
      try {
        setLoading(true);
        const rows = await executeQuery(db, sql);
        if (isMounted) {
          setData(rows);
          setError(null);
        }
      } catch (err: any) {
        if (isMounted) setError(err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    run();
    return () => { isMounted = false; }; // Cleanup to prevent memory leaks
  }, [db, sql]); // Only re-runs if DB or SQL string changes

  return { data, loading, error };
}