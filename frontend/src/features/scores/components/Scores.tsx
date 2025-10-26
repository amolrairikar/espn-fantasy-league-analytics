import { useEffect, useState } from 'react';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import type { LeagueData } from '@/components/types/league_data';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { ScoreboardCard } from '@/components/utils/ScoreboardCard';
import { SeasonSelect } from '@/components/utils/SeasonSelect';
import { WeekSelect } from '@/components/utils/WeekSelect';
import type { GetMatchups } from '@/features/standings/types';

function Scores() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const [selectedSeason, setSelectedSeason] = useState<string>();
  const [selectedWeek, setSelectedWeek] = useState<string | undefined>(undefined);
  const [matchups, setMatchups] = useState<GetMatchups['data']>([]);
  const [selectedMatchup, setSelectedMatchup] = useState<GetMatchups['data'][number] | null>(null);

  const { refetch: refetchWeeklyMatchups } = useGetResource<GetMatchups['data']>(`/matchups`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    season: selectedSeason,
    week_number: selectedWeek,
  });

  useEffect(() => {
    const fetchStatus = async () => {
      if (!selectedSeason || !selectedWeek) return;
      try {
        const response = await refetchWeeklyMatchups();
        if (response?.data?.data) {
          console.log(response);
          const sorted = [...response.data.data].sort((a, b) => {
            const aIsPlayoff = a.playoff_tier_type === 'WINNERS_BRACKET';
            const bIsPlayoff = b.playoff_tier_type === 'WINNERS_BRACKET';
            // Playoff first
            return aIsPlayoff === bIsPlayoff ? 0 : aIsPlayoff ? -1 : 1;
          });
          setMatchups(sorted);
          console.log(matchups);
        }
      } catch (err) {
        console.error(err);
      }
    };

    void fetchStatus();
  }, [refetchWeeklyMatchups, matchups, selectedSeason, selectedWeek]);

  return (
    <div className="space-y-6 my-6 px-4 md:px-0">
      <div className="flex flex-col items-center space-y-4 md:flex-row md:justify-center md:space-x-6 md:space-y-0">
        <SeasonSelect
          leagueData={leagueData}
          onSeasonChange={setSelectedSeason}
          className="w-full max-w-xs md:w-auto"
        />
        <WeekSelect season={selectedSeason} onWeekChange={setSelectedWeek} className="w-full max-w-xs md:w-auto" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 justify-items-center">
        {matchups.map((matchup) => {
          const matchupKey = `${matchup.team_a_member_id}-${matchup.team_b_member_id}-${matchup.week}`;
          return <ScoreboardCard key={matchupKey} matchup={matchup} onClick={() => setSelectedMatchup(matchup)} />;
        })}
        {selectedMatchup && (
          <MatchupSheet matchup={selectedMatchup} open={!!selectedMatchup} onClose={() => setSelectedMatchup(null)} />
        )}
      </div>
    </div>
  );
}

export default Scores;
