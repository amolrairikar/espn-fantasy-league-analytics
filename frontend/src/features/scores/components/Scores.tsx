import { useEffect, useMemo, useState } from 'react';
import { useDatabase } from '@/components/utils/DatabaseContext';
import { CustomSelect } from '@/components/utils/CustomSelectbox';
import { useDuckDbQuery } from '@/components/hooks/useDuckDbQuery';
import { ScoreboardCardSkeleton } from '@/features/scores/components/scoreboardCardSkeleton';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { ScoreboardCard } from '@/components/utils/ScoreboardCard';
import type { Matchup } from '@/features/scores/types';


function Scores() {
  const { db } = useDatabase();
  const [selectedSeason, setSelectedSeason] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<string | null>(null);
  const [selectedMatchup, setSelectedMatchup] = useState<Matchup | null>(null);

  const { data: seasons, error: seasonsQueryError, loading: loadingSeasons } = useDuckDbQuery<any>(
    db,
    `
    SELECT DISTINCT season FROM league_members ORDER BY SEASON DESC;
    `
  );

  const seasonOptions = seasons?.map(s => s.season) || [];
  const defaultSeason = seasonOptions.length > 0 ? seasonOptions.at(0) : "Loading...";

  const { data: weeks, error: weeksQueryError, loading: loadingWeeks } = useDuckDbQuery<any>(
    selectedSeason ? db : null,
    `
    SELECT DISTINCT week FROM league_matchups WHERE season = '${selectedSeason}' ORDER BY WEEK ASC;
    `
  );

  const weekOptions = weeks?.map(s => s.week) || [];
  const defaultWeek = weekOptions.length > 0 ? weekOptions.at(0) : "Loading...";

  // Sync defaults when data first arrives
  useEffect(() => {
    if (seasons && !selectedSeason) {
      setSelectedSeason(defaultSeason);
    }
    if (weeks && !selectedWeek) {
      setSelectedWeek(defaultWeek);
    }
  }, [seasons, weeks]);

  const { data: matchups, error: matchupsQueryError, loading: loadingMatchups } = useDuckDbQuery<any>(
    selectedSeason && selectedWeek ? db : null,
    `SELECT * FROM league_matchups WHERE season = '${selectedSeason}' AND week = ${selectedWeek}`
  );

  const { data: weeklyRecords, error: weeklyRecordsQueryError, loading: loadingWeeklyRecords } = useDuckDbQuery<any>(
    selectedSeason && selectedWeek ? db : null,
    `SELECT * FROM league_weekly_standings WHERE season = '${selectedSeason}' AND week = ${selectedWeek}`
  );


  const isLoading = (loadingSeasons || loadingWeeks || loadingMatchups || loadingWeeklyRecords);
  const activeError = (seasonsQueryError || weeksQueryError || matchupsQueryError|| weeklyRecordsQueryError);

  // Memoize the sorted data to prevent recalculating on every render
  const sortedMatchups = useMemo(() => {
    if (!matchups) return [];
    
    return [...matchups].sort((a, b) => {
      const aIsPlayoff = a.playoff_tier_type === 'WINNERS_BRACKET';
      const bIsPlayoff = b.playoff_tier_type === 'WINNERS_BRACKET';
      return aIsPlayoff === bIsPlayoff ? 0 : aIsPlayoff ? -1 : 1;
    });
  }, [matchups]);

  return (
    <div className="space-y-4 mt-2 mb-6 px-4 md:px-0">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl mx-auto">
        <div className="w-full flex justify-center">
          <div className="w-full max-w-50"> {/* Constrains width so they don't look like giant bars */}
            <CustomSelect
              title="Season"
              placeholder={selectedSeason || defaultSeason!}
              items={seasonOptions}
              onValueChange={(val) => setSelectedSeason(val)}
            />
          </div>
        </div>
        <div className="w-full flex justify-center">
          <div className="w-full max-w-50">
            <CustomSelect
              title="Week"
              placeholder={selectedWeek || defaultWeek!}
              items={weekOptions}
              onValueChange={(val) => setSelectedWeek(val)}
            />
          </div>
        </div>
      </div>

      {isLoading && <ScoreboardCardSkeleton />}
      
      {activeError && (
        <div className="p-8 text-center text-red-500">
          <h2>Error loading league data</h2>
          <p>{activeError instanceof Error ? activeError.message : activeError}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 justify-items-center max-w-4xl mx-auto">
        {sortedMatchups.map((matchup, index) => {
          const matchupKey = matchup.home_team_owner_id 
            ? `${matchup.home_team_owner_id}-${matchup.away_team_owner_id}-${matchup.week}`
            : `matchup-${index}`;

          return (
            <ScoreboardCard 
              key={matchupKey}
              matchup={matchup}
              team_records={weeklyRecords!}
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