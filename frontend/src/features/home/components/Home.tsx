// import { toast } from 'sonner';
import { useCallback, useEffect, useState } from 'react';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { getResource } from '@/components/hooks/genericGetRequest';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { usePostResource } from '@/components/hooks/genericPostRequest';
import { putResource } from '@/components/hooks/genericPutRequest';
import { LoadingButton } from '@/components/utils/loadingButton';
import type { GetLeagueMetadata } from '@/features/login/types';
import type { LeagueData } from '@/features/login/types';
import type {
  GetLeagueOnboardingStatus,
  PostLeagueOnboardingPayload,
  PostLeagueOnboardingResponse,
} from '@/features/home/types';
import { poll } from '@/features/home/utils/poll';

function Home() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  const [onboardedStatus, setOnboardedStatus] = useState<boolean | null>(null); // null = loading
  const [currentlyOnboarding, setCurrentlyOnboarding] = useState<boolean>(false);
  const [onboardingExecutionId, setOnboardingExecutionId] = useState<string | null>(null);

  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const { refetch: refetchLeagueMetadata } = useGetResource<GetLeagueMetadata>(`/leagues/${leagueData.leagueId}`, {
    platform: leagueData.platform,
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchLeagueMetadata();
        setOnboardedStatus(!!response.data?.data.onboarded_status);
      } catch (err) {
        console.error(err);
        setOnboardedStatus(false);
      }
    };

    void fetchStatus();
  }, [refetchLeagueMetadata]);

  const checkLeagueOnboarded = useCallback(async () => {
    try {
      const response = await refetchLeagueMetadata();
      console.log('League Metadata:', response.data);
      if (!response.data?.data.onboarded_status) {
        console.log('League not onboarded yet');
      } else {
        setOnboardedStatus(true);
        console.log('League is already onboarded');
      }
    } catch (error) {
      console.error('Error fetching league metadata:', error);
    }
  }, [refetchLeagueMetadata]);

  // Run checkLeagueOnboarded when the page loads or is refreshed
  useEffect(() => {
    void checkLeagueOnboarded();
  }, [checkLeagueOnboarded]);

  const { mutateAsync: PostOnboarding } = usePostResource<PostLeagueOnboardingPayload, PostLeagueOnboardingResponse>(
    '/onboard/',
  );

  const onboardLeagueData = async () => {
    setCurrentlyOnboarding(true);
    try {
      const leagueMetadata = await refetchLeagueMetadata();
      if (!leagueMetadata.data) {
        const errorMessage =
          'Unable to fetch league metadata to trigger onboarding. Please raise a GitHub issue if this persists.';
        console.error(errorMessage);
        throw new Error(errorMessage);
      }
      const payload = {
        league_id: leagueMetadata.data?.data.league_id,
        platform: leagueMetadata.data?.data.platform,
        privacy: leagueMetadata.data?.data.privacy,
        espn_s2: leagueMetadata.data?.data.espn_s2_cookie,
        swid: leagueMetadata.data?.data.swid_cookie,
        seasons: leagueMetadata.data?.data.seasons,
      };
      const result = await PostOnboarding(payload);
      setOnboardingExecutionId(result.data.execution_id);
      console.log('Onboarding execution id: ', onboardingExecutionId);

      // Poll for onboarding status
      await poll(() => getResource<GetLeagueOnboardingStatus>(`/onboard/${result.data.execution_id}`), {
        interval: 2000,
        timeout: 60000,
        validate: (status) => status.data.execution_status === 'SUCCEEDED',
      });
      console.log('Onboarding completed!');

      // Update metadata to set onboarded_status to true
      try {
        await putResource<PostLeagueOnboardingPayload, PostLeagueOnboardingResponse>(`/leagues/`, {
          league_id: leagueMetadata.data?.data.league_id,
          platform: leagueMetadata.data?.data.platform,
          privacy: leagueMetadata.data?.data.privacy,
          espn_s2: leagueMetadata.data?.data.espn_s2_cookie,
          swid: leagueMetadata.data?.data.swid_cookie,
          seasons: leagueMetadata.data?.data.seasons,
          onboarded_date: new Date().toISOString(),
          onboarded_status: true,
        });
        console.log('Updated league metadata to set onboarded_status to true');
        setOnboardedStatus(true);
      } catch (error) {
        console.error('Error updating league metadata:', error);
      }
    } catch (error) {
      console.error('Error onboarding league:', error);
      setCurrentlyOnboarding(false);
    } finally {
      setCurrentlyOnboarding(false);
    }
  };

  return (
    <div>
      {onboardedStatus === null ? (
        <p>Loading...</p>
      ) : onboardedStatus ? (
        <h1>Welcome to the home page!</h1>
      ) : (
        <div className="flex flex-col items-center gap-4">
          <h1 className="text-center">Nothing to see here. Click the button below to onboard your league data.</h1>
          <LoadingButton onClick={() => void onboardLeagueData()} loading={currentlyOnboarding}>
            Onboard
          </LoadingButton>
        </div>
      )}
    </div>
  );
}

export default Home;
