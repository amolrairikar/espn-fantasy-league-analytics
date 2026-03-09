import { useDuckDbQuery } from '@/components/hooks/useDuckDbQuery';
import { useDatabase } from '@/components/utils/DatabaseContext';
import AllTimeRecords from '@/features/home/components/AllTimeRecords';

function Home() {
  const { db } = useDatabase();

  const { data: championsData, error: championsQueryError } = useDuckDbQuery<any>(
    db,
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
    db,
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
    db,
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
    db,
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
    db,
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
    db,
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
    db,
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
    db,
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
    db,
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