import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import type { LeagueData } from '@/components/types/league_data';
import DraftBoard from '@/features/draft/components/DraftBoard';
import { SeasonSelect } from '@/components/utils/SeasonSelect';
import { fetchDraftResults } from '@/api/draft_results/api_calls';
import { DraftBoardSkeleton } from '@/features/draft/components/DraftPickBoardSkeleton';

function useFetchDraftResults(
  league_id: string,
  platform: string,
  season: string,
) {
  return useQuery({
    queryKey: ['draft_results', league_id, platform, season],
    queryFn: () => fetchDraftResults(
      league_id,
      platform,
      season,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!season, // only run if input args are available
  });
};

function Draft() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);

  const [selectedSeason, setSelectedSeason] = useState<string>();
  // const [draftResults, setDraftResults] = useState<GetDraftResults['data']>([]);

  const { data: rawDraftData, isLoading: loadingDraftResults } = useFetchDraftResults(
    leagueData!.leagueId,
    leagueData!.platform,
    selectedSeason!,
  );

  // Early return if saving league data to local storage fails
  if (!leagueData) {
    return (
      <p>
        League credentials not found in local browser storage. Please try logging in again and if the issue persists,
        create a support ticket.
      </p>
    );
  };

  const draftResults = useMemo(() => {
    if (!rawDraftData?.data) return [];
    return rawDraftData.data;
  }, [rawDraftData]);

  return (
      <div className="space-y-6 my-6 px-4 md:px-0">

      {/* Season Selector */}
      <div className="flex flex-col items-center space-y-4 md:flex-row md:justify-center md:space-x-6 md:space-y-0">
        <SeasonSelect
          leagueData={leagueData}
          selectedSeason={selectedSeason}
          onSeasonChange={setSelectedSeason}
          className="w-full max-w-xs md:w-auto"
        />
      </div>

      {/* Draft Board Cards */}
      {loadingDraftResults ? (
        <DraftBoardSkeleton />
      ) : (
        <DraftBoard draftResults={draftResults} />
      )}

    </div>
    );
}

export default Draft;