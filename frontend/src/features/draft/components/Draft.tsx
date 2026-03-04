import { useEffect, useState } from 'react';
import { useDatabase } from '@/components/utils/DatabaseContext';
import { CustomSelect } from '@/components/utils/CustomSelectbox';
import { useDuckDbQuery } from '@/components/hooks/useDuckDbQuery';
import DraftBoard from '@/features/draft/components/DraftBoard';
import { DraftBoardSkeleton } from '@/features/draft/components/DraftPickBoardSkeleton';

function Draft() {
  const { db } = useDatabase();

  const [selectedSeason, setSelectedSeason] = useState<string>();

  const { data: seasons, error: seasonsQueryError, loading: loadingSeasons } = useDuckDbQuery<any>(
    db,
    `
    SELECT DISTINCT season FROM league_members ORDER BY SEASON DESC;
    `
  );

  const seasonOptions = seasons?.map(s => s.season) || [];
  const defaultSeason = seasonOptions.length > 0 ? seasonOptions.at(0) : "Loading...";

  const { data: draftResults, error: draftResultsQueryError, loading: loadingDraftResults } = useDuckDbQuery<any>(
    selectedSeason ? db : null,
    `SELECT * FROM league_draft_results  WHERE season = '${selectedSeason}'`
  );

  // Sync defaults when data first arrives
  useEffect(() => {
    if (seasons && !selectedSeason) {
      setSelectedSeason(defaultSeason);
    }
  }, [seasons]);

  const isLoading = (loadingSeasons || loadingDraftResults);
  const activeError = (seasonsQueryError || draftResultsQueryError);

  return (
      <div className="space-y-6 my-6 px-4 md:px-0">

      {/* Season Selector */}
      <div className="flex flex-col items-center space-y-4 md:flex-row md:justify-center md:space-x-6 md:space-y-0">
        <CustomSelect
          title="Season"
          placeholder={selectedSeason || defaultSeason!}
          items={seasonOptions}
          onValueChange={(val) => setSelectedSeason(val)}
        />
      </div>

      {activeError && (
        <div className="p-8 text-center text-red-500">
          <h2>Error loading league data</h2>
          <p>{activeError instanceof Error ? activeError.message : activeError}</p>
        </div>
      )}

      {/* Draft Board Cards */}
      {isLoading ? (<DraftBoardSkeleton />) : (<DraftBoard draftResults={draftResults!} />)}

    </div>
    );
}

export default Draft;
