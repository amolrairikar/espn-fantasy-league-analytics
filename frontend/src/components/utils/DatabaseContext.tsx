import * as duckdb from '@duckdb/duckdb-wasm';
import { createContext, useContext, useEffect, useState } from 'react';
import { Skeleton } from "@/components/ui/skeleton";
import { useDuckDB } from '@/components/hooks/useDuckDb';
import { ensureLatestDatabase } from '@/components/utils/syncDuckDb';

interface DatabaseContextType {
  db: duckdb.AsyncDuckDB | null;
  isReady: boolean;
}

const DatabaseContext = createContext<DatabaseContextType | null>(null);

export const DatabaseProvider = ({ children }: { children: React.ReactNode }) => {
  const { db, loading: dbLoading, error: dbError } = useDuckDB();
  const [isSyncing, setIsSyncing] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);

  useEffect(() => {
    // Reset ready state immediately so queries don't fire against a stale/unopened instance
    setIsReady(false);

    async function sync() {
    if (!db) return;

    try {
        setIsSyncing(true);
        await ensureLatestDatabase(db);
        console.log("Database is up to date.");
        setIsReady(true);
    } catch (err: any) {
        console.error("Sync failed:", err);
        setSyncError(err.message || "Failed to sync database.");
    } finally {
        setIsSyncing(false);
    }
    }

    sync();
  }, [db]); // Runs as soon as DuckDB is ready

  const activeError = (dbError || syncError);
  if (activeError) {
    return (
      <div className="p-8 text-center text-red-500">
        <h2>Error loading league database</h2>
        <p>{activeError instanceof Error ? activeError.message : activeError}</p>
      </div>
    );
  }

  // Centralized loading UI
  if (dbLoading || (isSyncing && !isReady)) {
    return (
      <div className="flex h-screen flex-col items-center justify-center space-y-4 p-12">
        <h2 className="text-xl font-semibold animate-pulse text-slate-700">
          {dbLoading ? "Initializing Database..." : "Syncing Latest Stats..."}
        </h2>
        <Skeleton className="h-5 w-64 rounded-full" />
      </div>
    );
  }

  return (
    <DatabaseContext.Provider value={{ db, isReady }}>
      {children}
    </DatabaseContext.Provider>
  );
};

// Export the hook for easy usage in components
export const useDatabase = () => {
  const context = useContext(DatabaseContext);
  if (!context) {
    throw new Error("useDatabase must be used within a DatabaseProvider");
  }
  return context;
};