import { useEffect, useState } from 'react';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import type { LeagueData } from '@/components/types/league_data';
import DraftBoard from '@/features/draft/components/DraftBoard';

import type { GetDraftResults } from '@/features/draft/types';
import { SeasonSelect } from '@/components/utils/SeasonSelect';

function Draft() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const [selectedSeason, setSelectedSeason] = useState<string>();
  const [draftResults, setDraftResults] = useState<GetDraftResults['data']>([]);

  const { refetch: refetchDraftData } = useGetResource<GetDraftResults['data']>(`/draft-results`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    season: selectedSeason,
  });

  useEffect(() => {
    const fetchStatus = async () => {
      if (!selectedSeason) return;
      try {
        const response = await refetchDraftData();
        if (response?.data?.data) {
          setDraftResults(response.data.data);
          console.log('Draft Results:', response.data.data);
        }
      } catch (err) {
        console.error(err);
      }
    };

    void fetchStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSeason]);

  // Clear draft results when season or week changes to avoid showing stale data
  useEffect(() => {
    setDraftResults([]);
  }, [selectedSeason]);

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
      <DraftBoard draftResults={draftResults} />

    </div>
    );
}

export default Draft;