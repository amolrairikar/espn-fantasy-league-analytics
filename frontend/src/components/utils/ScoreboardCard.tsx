import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchWeeklyStandings } from '@/api/standings/api_calls';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import type { LeagueData } from '@/features/login/types';
import type { GetMatchups } from '@/api/matchups/types';
import type { GetWeeklyStandings } from '@/features/standings/types';

interface ScoreboardCardProps {
  matchup: GetMatchups['data'][number];
  onClick?: () => void;
}

function useFetchWeeklyStandings(
  league_id: string,
  platform: string,
  standings_type: string,
  season: string,
  team: string,
  week: string,
) {
  return useQuery({
    queryKey: ['weekly', league_id, platform, standings_type, season, team, week],
    queryFn: () => fetchWeeklyStandings(
      league_id,
      platform,
      standings_type,
      season,
      team,
      week,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!standings_type, // only run if input args are available
  });
};

export function ScoreboardCard({ matchup, onClick }: ScoreboardCardProps) {
  const isTeamAWinner = matchup.winner === matchup.team_a_owner_id;
  const isTeamBWinner = matchup.winner === matchup.team_b_owner_id;
  const isPlayoff = matchup.playoff_tier_type === 'WINNERS_BRACKET';
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);

  const { data: rawWeeklyStandingsTeamA } = useFetchWeeklyStandings(
    leagueData!.leagueId,
    leagueData!.platform,
    'weekly',
    matchup.season,
    matchup.team_a_owner_id,
    matchup.week,
  );

  const { data: rawWeeklyStandingsTeamB } = useFetchWeeklyStandings(
    leagueData!.leagueId,
    leagueData!.platform,
    'weekly',
    matchup.season,
    matchup.team_b_owner_id,
    matchup.week,
  );

  const teamAStandings = useMemo<GetWeeklyStandings['data'] | null>(() => {
    if (!leagueData || !matchup) return null;
    return rawWeeklyStandingsTeamA?.data ?? null;
  }, [rawWeeklyStandingsTeamA, leagueData, matchup]);

  const teamBStandings = useMemo<GetWeeklyStandings['data'] | null>(() => {
    if (!leagueData || !matchup) return null;
    return rawWeeklyStandingsTeamB?.data ?? null;
  }, [rawWeeklyStandingsTeamB, leagueData, matchup]);

  const teamARecord =
    teamAStandings && teamAStandings.length > 0
      ? `${teamAStandings[0].wins}-${teamAStandings[0].losses}-${teamAStandings[0].ties}`
      : '--';

  const teamBRecord =
    teamBStandings && teamBStandings.length > 0
      ? `${teamBStandings[0].wins}-${teamBStandings[0].losses}-${teamBStandings[0].ties}`
      : '--';

  return (
    <div className="relative w-full max-w-md mx-auto cursor-pointer" onClick={onClick}>
      {/* PLAYOFF badge */}
      {isPlayoff && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-md shadow-sm border border-border">
          PLAYOFF
        </div>
      )}

      {/* Scoreboard card */}
      <div className="bg-card shadow rounded-md p-4 w-full">
        {/* Team A */}
        <div className="flex justify-between items-center py-2 border-b border-border">
          <div className="text-left">
            <div className={`text-lg ${isTeamAWinner ? 'font-bold' : ''}`}> {matchup.team_a_team_name} </div>
            <div className={`text-sm text-muted-foreground ${isTeamAWinner ? 'font-bold text-foreground' : ''}`}>
              {matchup.team_a_owner_full_name}{' '}
              {matchup.playoff_tier_type === 'NONE' && (
                <span className="text-xs text-muted-foreground">({teamARecord})</span>
              )}
            </div>
          </div>
          <div className={`text-right text-lg ${isTeamAWinner ? 'font-bold' : ''}`}>
            {Number(matchup.team_a_score).toFixed(2)}
          </div>
        </div>

        {/* Team B */}
        <div className="flex justify-between items-center py-2">
          <div className="text-left">
            <div className={`text-lg ${isTeamBWinner ? 'font-bold' : ''}`}> {matchup.team_b_team_name} </div>
            <div className={`text-sm text-muted-foreground ${isTeamBWinner ? 'font-bold text-foreground' : ''}`}>
              {matchup.team_b_owner_full_name}{' '}
              {matchup.playoff_tier_type === 'NONE' && (
                <span className="text-xs text-muted-foreground">({teamBRecord})</span>
              )}
            </div>
          </div>
          <div className={`text-right text-lg ${isTeamBWinner ? 'font-bold' : ''}`}>
            {Number(matchup.team_b_score).toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}
