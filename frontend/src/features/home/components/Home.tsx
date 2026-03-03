import { useEffect, useState } from 'react';
import { useDuckDB } from '@/components/hooks/useDuckDb';
import { ensureLatestDatabase } from '@/components/utils/syncDuckDb';
import { useDuckDbQuery } from '@/components/hooks/useDuckDbQuery';
import { Skeleton } from '@/components/ui/skeleton';

function Home() {
  const { db, loading: dbLoading, error: dbError } = useDuckDB();
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);

  useEffect(() => {
    async function sync() {
      if (!db) return;

      try {
        setIsSyncing(true);
        await ensureLatestDatabase(db);
        console.log("Database is up to date.");
      } catch (err: any) {
        console.error("Sync failed:", err);
        setSyncError(err.message || "Failed to sync database.");
      } finally {
        setIsSyncing(false);
      }
    }

    sync();
  }, [db]); // Runs as soon as DuckDB is ready

  useEffect(() => {
    async function debugTables() {
      if (!db || isSyncing) return;
      const conn = await db.connect();
      const tables = await conn.query("SHOW TABLES");
      console.log("Tables found in DuckDB-Wasm:", tables.toArray().map(r => r.toJSON()));
      await conn.close();
    }
    debugTables();
  }, [db, isSyncing]);

  const { data: members, loading: queryLoading, error: queryError } = useDuckDbQuery<any>(
    db, 
    !isSyncing ? "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main';" : "" 
  );

  const activeError = dbError || syncError || queryError;
  if (activeError) {
    return (
      <div className="p-8 text-center text-red-500">
        <h2>Error loading league data</h2>
        <p>{activeError instanceof Error ? activeError.message : activeError}</p>
      </div>
    );
  }

  // Handle loading states
  if (dbLoading || isSyncing) {
    return (
      <div className="flex flex-col items-center justify-center space-y-4 p-12">
        <h2 className="text-xl font-semibold animate-pulse">
          {dbLoading ? "Initializing Database..." : "Syncing Latest Stats..."}
        </h2>
        <Skeleton className="h-5 w-62.5 rounded-full" />
      </div>
    );
  }

  return (
    <ul>
      {members?.map(m => <li key={m.id}>{m.name}</li>)}
    </ul>
  );
}

export default Home;