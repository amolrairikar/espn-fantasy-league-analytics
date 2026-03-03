import { useEffect, useState } from 'react';
import { useDuckDB } from '@/components/hooks/useDuckDb';
import { ensureLatestDatabase } from '@/components/utils/syncDuckDb';
import { useDuckDbQuery } from '@/components/hooks/useDuckDbQuery';
import { Skeleton } from '@/components/ui/skeleton';
import AllTimeRecords from '@/features/home/components/AllTimeRecords';

function Home() {
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

  // Only pass db after sync has fully resolved to prevent queries racing with the sync
  const { data: championsData, error: championsQueryError } = useDuckDbQuery<any>(
    isReady ? db : null,
    `
    SELECT
      owner_full_name, 
      COUNT(owner_full_name) AS championships_won
    FROM league_postseason_teams
    WHERE status = 'LEAGUE_CHAMPION'
    GROUP BY owner_full_name
    ORDER BY championships_won DESC, owner_full_name ASC;
    `
  );

  const { data: topTeamScores, error: topTeamScoresQueryError } = useDuckDbQuery<any>(
    isReady ? db : null,
    `
    SELECT
      owner_name AS owner_full_name,
      score AS points_scored,
      season,
      week,
      owner_id
    FROM league_top_and_bottom_scores
    WHERE category = 'TOP 10'
    ORDER BY score DESC;
    `
  );

  const { data: bottomTeamScores, error: bottomTeamScoresQueryError } = useDuckDbQuery<any>(
    isReady ? db : null,
    `
    SELECT
      owner_name AS owner_full_name,
      score AS points_scored,
      season,
      week,
      owner_id
    FROM league_top_and_bottom_scores
    WHERE category = 'BOTTOM 10'
    ORDER BY score ASC;
    `
  );

  const { data: topQbScores, error: topQbScoresQueryError } = useDuckDbQuery<any>(
    isReady ? db : null,
    `
    SELECT
      owner_id,
      points AS points_scored,
      season,
      week,
      full_name AS player_name
    FROM league_top_player_performances
    WHERE position = 'QB'
    ORDER BY points DESC;
    `
  );

  const { data: topRbScores, error: topRbScoresQueryError } = useDuckDbQuery<any>(
    isReady ? db : null,
    `
    SELECT
      owner_id,
      points AS points_scored,
      season,
      week,
      full_name AS player_name
    FROM league_top_player_performances
    WHERE position = 'RB'
    ORDER BY points DESC;
    `
  );

  const { data: topWrScores, error: topWrScoresQueryError } = useDuckDbQuery<any>(
    isReady ? db : null,
    `
    SELECT
      owner_id,
      points AS points_scored,
      season,
      week,
      full_name AS player_name
    FROM league_top_player_performances
    WHERE position = 'WR'
    ORDER BY points DESC;
    `
  );

  const { data: topTeScores, error: topTeScoresQueryError } = useDuckDbQuery<any>(
    isReady ? db : null,
    `
    SELECT
      owner_id,
      points AS points_scored,
      season,
      week,
      full_name AS player_name
    FROM league_top_player_performances
    WHERE position = 'TE'
    ORDER BY points DESC;
    `
  );

  const { data: topDstScores, error: topDstScoresQueryError } = useDuckDbQuery<any>(
    isReady ? db : null,
    `
    SELECT
      owner_id,
      points AS points_scored,
      season,
      week,
      full_name AS player_name
    FROM league_top_player_performances
    WHERE position = 'D/ST'
    ORDER BY points DESC
    LIMIT 10;
    `
  );

  const { data: topKScores, error: topKScoresQueryError } = useDuckDbQuery<any>(
    isReady ? db : null,
    `
    SELECT
      owner_id,
      points AS points_scored,
      season,
      week,
      full_name AS player_name
    FROM league_top_player_performances
    WHERE position = 'K'
    ORDER BY points DESC;
    `
  );

  const activeError = (
    dbError || 
    syncError || 
    championsQueryError || 
    topTeamScoresQueryError ||
    bottomTeamScoresQueryError ||
    topQbScoresQueryError ||
    topRbScoresQueryError ||
    topWrScoresQueryError ||
    topTeScoresQueryError ||
    topDstScoresQueryError ||
    topKScoresQueryError
  );
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
    <AllTimeRecords 
      champions={championsData} 
      topScores={topTeamScores} 
      bottomScores={bottomTeamScores}
      qbScores={topQbScores}
      rbScores={topRbScores}
      wrScores={topWrScores}
      teScores={topTeScores}
      dstScores={topDstScores}
      kScores={topKScores}
    />
  );
}

export default Home;