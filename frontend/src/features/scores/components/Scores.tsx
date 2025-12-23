import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query'
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import type { LeagueData } from '@/components/types/league_data';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { ScoreboardCard } from '@/components/utils/ScoreboardCard';
import { ScoreboardCardSkeleton } from '@/features/scores/components/ScoresSkeleton';
import { SeasonSelect } from '@/components/utils/SeasonSelect';
import { WeekSelect } from '@/components/utils/WeekSelect';
import type { GetMatchups } from '@/api/matchups/types';
import { fetchMatchups } from '@/api/matchups/api_calls';

type Matchup = GetMatchups['data'] extends (infer T)[] ? T : never;

function useFetchMatchups(
  league_id: string,
  platform: string,
  playoff_filter: string,
  week_number: string,
  season: string,
) {
  return useQuery({
    queryKey: ['matchups', league_id, platform, playoff_filter, week_number, season],
    queryFn: () => fetchMatchups(
      league_id,
      platform,
      playoff_filter,
      undefined, // team1_id
      undefined, // team2_id
      week_number,
      season,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!playoff_filter && !!week_number && !!season, // only run if input args are available
  });
};

function Scores() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);

  const [selectedSeason, setSelectedSeason] = useState<string>();
  const [selectedWeek, setSelectedWeek] = useState<string | undefined>(undefined);
  const [selectedMatchup, setSelectedMatchup] = useState<Matchup | null>(null);

  const { data: matchupResponse, isLoading, isError } = useFetchMatchups(
    leagueData!.leagueId,
    leagueData!.platform,
    'include',
    selectedWeek!,
    selectedSeason!,
  );

  // Memoize the sorted data to prevent recalculating on every render
  const sortedMatchups = useMemo(() => {
    if (!matchupResponse?.data || !Array.isArray(matchupResponse.data)) return [];
    
    return [...matchupResponse.data].sort((a, b) => {
      const aIsPlayoff = a.playoff_tier_type === 'WINNERS_BRACKET';
      const bIsPlayoff = b.playoff_tier_type === 'WINNERS_BRACKET';
      return aIsPlayoff === bIsPlayoff ? 0 : aIsPlayoff ? -1 : 1;
    });
  }, [matchupResponse]);

  // Early return if saving league data to local storage fails
  if (!leagueData) {
    return (
      <p>
        League credentials not found in local browser storage. Please try logging in again and if the issue persists,
        create a support ticket.
      </p>
    );
  }

  return (
    <div className="space-y-6 my-6 px-4 md:px-0">
      <div className="flex flex-col items-center space-y-4 md:flex-row md:justify-center md:space-x-6 md:space-y-0">
        <SeasonSelect
          leagueData={leagueData}
          selectedSeason={selectedSeason}
          onSeasonChange={setSelectedSeason}
          className="w-full max-w-xs md:w-auto"
        />
        <WeekSelect season={selectedSeason} onWeekChange={setSelectedWeek} className="w-full max-w-xs md:w-auto" />
      </div>
      {isLoading && <ScoreboardCardSkeleton/>}
      {isError && <p className="text-center text-red-500">Error loading data.</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 justify-items-center">
        {sortedMatchups.map((matchup) => {
          // Fallback key using index if IDs are missing
          const matchupKey = `${matchup.team_a_owner_id}-${matchup.team_b_owner_id}-${matchup.week}`;
          return (
            <ScoreboardCard 
              key={matchupKey} 
              matchup={matchup} 
              onClick={() => setSelectedMatchup(matchup)} 
            />
          );
        })}
      </div>
      {selectedMatchup && (
        <MatchupSheet 
          matchup={selectedMatchup} 
          open={!!selectedMatchup} 
          onClose={() => setSelectedMatchup(null)} 
        />
      )}
    </div>
  );
}

export default Scores;
