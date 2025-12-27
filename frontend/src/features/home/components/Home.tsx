import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { LoadingButton } from '@/components/utils/loadingButton';
import type { LeagueData } from '@/features/login/types';
import AllTimeRecords from '@/features/home/components/AllTimeRecords';
import { poll } from '@/features/home/utils/poll';
import { getLeagueOnboardingStatus, postLeagueOnboarding } from '@/api/onboarding/api_calls';
import { getLeagueMetadata, putLeagueMetadata } from '@/api/league_metadata/api_calls';

function useLeagueMetadata(leagueId: string, platform: string) {
  return useQuery({
    queryKey: ['leagueMetadata', leagueId, platform],
    queryFn: () => getLeagueMetadata(leagueId, platform),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!leagueId && !!platform, // only run if leagueId and platform are available
  });
};

function Home() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  const [currentlyOnboarding, setCurrentlyOnboarding] = useState<boolean>(false);
  const queryClient = useQueryClient();

  // Hook must be called before any returns
  const { data: leagueMetadata, isLoading, isError, error } = useLeagueMetadata(
    leagueData!.leagueId,
    leagueData!.platform,
  );

  // Early return if saving league data to local storage fails
  if (!leagueData) {
    return (
      <p>
        League credentials not found in local browser storage. Please try logging in again and if the issue persists,
        create a support ticket.
      </p>
    );
  }

  if (isLoading) {
    return <p className="text-center">Loading...</p>;
  }

  if (isError || !leagueMetadata || !leagueMetadata.data) {
    console.error('Error getting league metadata', { isError, error, leagueMetadata });
    return <p>Error getting league metadata. Please try reloading and if the issue persists raise a support ticket.</p>;
  }

  const { league_id, platform, privacy, espn_s2_cookie, swid_cookie, seasons, onboarded_date, onboarded_status } =
    leagueMetadata.data;

  const onboarded = Boolean(onboarded_status && onboarded_date);

  const onboardLeagueData = async () => {
    setCurrentlyOnboarding(true);
    try {
      const payload = {
        league_id,
        platform,
        privacy,
        espn_s2: espn_s2_cookie ?? '',
        swid: swid_cookie ?? '',
        seasons,
      };
      const result = await postLeagueOnboarding(payload);
      if (!result.data.execution_id) {
        console.error('Onboarding response missing execution_id');
        toast.error('Error occurred while onboarding league. Please try again.');
        return;
      }
      const execution_id = result.data.execution_id;
      console.log('Onboarding execution id: ', execution_id);

      await poll(() => getLeagueOnboardingStatus(execution_id), {
        interval: 2000,
        timeout: 60000,
        validate: (status) => status.data?.execution_status === 'SUCCEEDED',
      });

      // Update metadata to set onboarded_status to true
      try {
        await putLeagueMetadata({
          league_id,
          platform,
          privacy,
          espn_s2: espn_s2_cookie,
          swid: swid_cookie,
          seasons,
          onboarded_date: new Date().toISOString(),
          onboarded_status: true,
        });
        console.log('Onboarding completed!');
        toast.success('Onboarding completed successfully!');
        // Refetch league metadata after onboarding completed
        queryClient.invalidateQueries({
          queryKey: ['leagueMetadata', league_id, platform]
        });
      } catch (error) {
        console.error('Error updating league metadata:', error);
      }
    } catch (error) {
      console.error('Error onboarding league:', error);
      toast.error('Error occurred while onboarding')
      setCurrentlyOnboarding(false);
    } finally {
      setCurrentlyOnboarding(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-4">
      {onboarded ? (
        <AllTimeRecords />
      ) : (
        <>
          <h1 className="text-center">Nothing to see here. Click the button below to onboard your league data.</h1>
          <LoadingButton onClick={() => void onboardLeagueData()} loading={currentlyOnboarding}>
            Onboard
          </LoadingButton>
        </>
      )}
    </div>
  );
}

export default Home;
