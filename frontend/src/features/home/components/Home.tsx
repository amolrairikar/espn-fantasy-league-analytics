import { useState } from 'react';
import { toast } from 'sonner';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { getResource, useGetResource } from '@/components/hooks/genericGetRequest';
import { usePostResource } from '@/components/hooks/genericPostRequest';
import { putResource } from '@/components/hooks/genericPutRequest';
import { LoadingButton } from '@/components/utils/loadingButton';
import type { LeagueData } from '@/features/login/types';
import type { GetLeagueMetadata } from '@/features/login/types';
import type {
  OnboardResponse,
  OnboardStatusResponse,
  PostLeagueOnboardingPayload,
  PutLeagueMetadataPayload,
} from '@/features/home/types';
import { poll } from '@/features/home/utils/poll';

function Home() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  const [currentlyOnboarding, setCurrentlyOnboarding] = useState<boolean>(false);

  const {
    data,
    refetch: refetchLeagueMetadata,
    isLoading,
    isError,
  } = useGetResource<GetLeagueMetadata['data']>(
    leagueData ? `/leagues/${leagueData.leagueId}` : '',
    { platform: leagueData?.platform },
    { enabled: !!leagueData?.leagueId && !!leagueData?.platform },
  );

  const { mutateAsync: PostOnboarding } = usePostResource<PostLeagueOnboardingPayload, OnboardResponse>('/onboard');

  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (isError || !data?.data) {
    return (
      <p>
        Unable to retrieve your fantasy football league information. Please try refreshing and if the issue persists,
        raise a GitHub issue.
      </p>
    );
  }

  const { league_id, platform, privacy, espn_s2_cookie, swid_cookie, seasons, onboarded_date, onboarded_status } =
    data.data;

  const onboarded = Boolean(onboarded_status && onboarded_date);

  const onboardLeagueData = async () => {
    setCurrentlyOnboarding(true);
    try {
      const payload = {
        league_id,
        platform,
        privacy,
        espn_s2: espn_s2_cookie,
        swid: swid_cookie,
        seasons,
      };
      const result = await PostOnboarding(payload);
      if (!result.data?.execution_id) {
        const errorMessage = 'Onboarding response missing execution_id';
        console.error(errorMessage);
        toast.error(errorMessage);
        return;
      }
      const execution_id = result.data.execution_id;
      console.log('Onboarding execution id: ', execution_id);

      await poll(() => getResource<OnboardStatusResponse>(`/onboard/${execution_id}`), {
        interval: 2000,
        timeout: 60000,
        validate: (status) => status.data?.execution_status === 'SUCCEEDED',
      });
      console.log('Onboarding completed!');

      // Update metadata to set onboarded_status to true
      try {
        await putResource<PutLeagueMetadataPayload, OnboardResponse>(`/leagues/${league_id}`, {
          league_id,
          platform,
          privacy,
          espn_s2: espn_s2_cookie,
          swid: swid_cookie,
          seasons,
          onboarded_date: new Date().toISOString(),
          onboarded_status: true,
        });
        console.log('Updated league metadata to set onboarded_status to true');
        await refetchLeagueMetadata();
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

  if (isError || !league_id || !platform || !privacy || !espn_s2_cookie || !swid_cookie || !seasons) {
    return (
      <p>
        Unable to retrieve your fantasy football league information. Please try refreshing and if the issue persists,
        raise a GitHub issue.
      </p>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4">
      {onboarded ? (
        <h1>Welcome to the home page!</h1>
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
