import { useEffect, useState } from 'react';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import type { LeagueData } from '@/features/login/types';
import type { GetMatchupsBetweenTeams, GetWeeklyStandings } from '@/features/standings/types';

interface ScoreboardCardProps {
  matchup: GetMatchupsBetweenTeams['data'][number];
  onClick?: () => void;
}

export function ScoreboardCard({ matchup, onClick }: ScoreboardCardProps) {
  const isTeamAWinner = matchup.winner === matchup.team_a_owner_id;
  const isTeamBWinner = matchup.winner === matchup.team_b_owner_id;
  const isPlayoff = matchup.playoff_tier_type === 'WINNERS_BRACKET';
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  const [teamAStandings, setTeamAStandings] = useState<GetWeeklyStandings['data'] | null>(null);
  const [teamBStandings, setTeamBStandings] = useState<GetWeeklyStandings['data'] | null>(null);

  const { refetch: refetchWeeklyStandingsTeamA } = useGetResource<GetWeeklyStandings['data']>(`/standings`, {
    league_id: leagueData?.leagueId,
    platform: leagueData?.platform,
    standings_type: 'weekly',
    season: matchup.season,
    team: matchup.team_a_owner_id,
    week: matchup.week,
  });

  const { refetch: refetchWeeklyStandingsTeamB } = useGetResource<GetWeeklyStandings['data']>(`/standings`, {
    league_id: leagueData?.leagueId,
    platform: leagueData?.platform,
    standings_type: 'weekly',
    season: matchup.season,
    team: matchup.team_b_owner_id,
    week: matchup.week,
  });

  // Fetch standings when matchup data changes ---
  useEffect(() => {
    const fetchStandings = async () => {
      if (!leagueData || !matchup) return;
      try {
        const [teamAResponse, teamBResponse] = await Promise.all([
          refetchWeeklyStandingsTeamA(),
          refetchWeeklyStandingsTeamB(),
        ]);
        console.log(teamAResponse);
        console.log(teamBResponse);
        setTeamAStandings(teamAResponse?.data?.data ?? null);
        setTeamBStandings(teamBResponse?.data?.data ?? null);
      } catch (err) {
        console.error('Error fetching standings:', err);
      }
    };

    void fetchStandings();
  }, [refetchWeeklyStandingsTeamA, refetchWeeklyStandingsTeamB, leagueData, matchup]);

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
            {parseFloat(matchup.team_a_score).toFixed(2)}
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
            {parseFloat(matchup.team_b_score).toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}
