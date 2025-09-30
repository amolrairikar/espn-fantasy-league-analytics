import axios from 'axios';
import { useCallback, useEffect, useState } from 'react';
import { useLocalStorage } from './hooks/useLocalStorage';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import type { LeagueData } from './components/types/league_data';
import apiHeader from './components/utils/api_header';
import type { ApiResponse } from './components/types/api_response';

interface LeagueInformation {
  league_id: string;
  privacy: string;
  platform: string;
  swid_cookie: string;
  seasons: string[];
  onboarded_date: string;
  espn_s2_cookie: string;
  PK: string;
  SK: string;
}

interface OnboardingResponse {
  execution_id: string;
}

interface OnboardingPollResponse {
  execution_status: string;
}

function Home() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  const [leagueOnboarded, setLeagueOnboarded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [onboardingStatusId, setOnboardingStatusId] = useState('');
  const [onboardingStatus, setOnboardingStatus] = useState('');
  const POLL_INTERVAL = 5000; // 5 seconds

  // Ensure leagueMetadata exists and has leagueId field
  if (!leagueData || !leagueData.leagueId) {
    throw new Error('Invalid league metadata: missing leagueId.');
  }

  // Function to get the current season year
  function getCurrentSeasonYear(): number {
    const today = new Date();
    const month = today.getMonth();
    const year = today.getFullYear();
    return month < 8 ? year - 1 : year; // Before September → previous year, else current year
  }

  const latestSeason = getCurrentSeasonYear();

  const checkLeagueOnboarded = useCallback(async () => {
    try {
      const response = await axios.get<ApiResponse>(`${import.meta.env.VITE_API_BASE_URL}/teams/`, {
        params: {
          league_id: leagueData.leagueId,
          platform: leagueData.platform,
          season: latestSeason,
          team_id: '1', // hardcoded for now, assumption is that leagues should have at least one team
        },
        headers: apiHeader,
      });
      if (response.status === 200) {
        setLeagueOnboarded(true);
      }
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        if (error.response.status === 404) {
          console.log('League data not onboarded yet');
        } else {
          toast.error('An unexpected error occurred. Please try again, and if the error persists contact us.');
        }
      }
      return false;
    }
  }, [leagueData.leagueId, leagueData.platform, latestSeason]);

  // Run the onboarding check on mount
  useEffect(() => {
    void checkLeagueOnboarded();
  }, [checkLeagueOnboarded]);

  const getLeagueMetadata = async (): Promise<LeagueInformation | undefined> => {
    try {
      const response = await axios.get<ApiResponse<LeagueInformation>>(
        `${import.meta.env.VITE_API_BASE_URL}/leagues/${leagueData.leagueId}`,
        {
          params: {
            platform: leagueData.platform,
          },
          headers: apiHeader,
        },
      );
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Axios error:', error.response?.data || error.message);
      } else {
        console.error('Unexpected error:', error);
      }
    }
  };

  const pollOnboardingStatus = useCallback(async () => {
    try {
      const response = await axios.get<ApiResponse<OnboardingPollResponse>>(
        `${import.meta.env.VITE_API_BASE_URL}/onboarding/${onboardingStatusId}`,
      );
      const status = response.data.data.execution_status;
      setOnboardingStatus(status);
      if (status === 'COMPLETED') {
        setOnboardingStatusId('');
      } else if (status === 'FAILED') {
        setOnboardingStatusId('');
        toast.error('Onboarding failed. Please reach out to us if this error persists.');
      }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Axios error:', error.response?.data || error.message);
        toast.error('Error checking onboarding status.');
      } else {
        console.error('Unexpected error:', error);
        toast.error('Unexpected error checking onboarding status.');
      }
    }
  }, [onboardingStatusId]);

  const onboardLeagueData = async () => {
    setLoading(true);
    try {
      const metadata = await getLeagueMetadata();
      if (!metadata) {
        throw new Error('Missing league metadata.');
      } else {
        const response = await axios.post<ApiResponse<OnboardingResponse>>(
          `${import.meta.env.VITE_API_BASE_URL}/onboard/${metadata.league_id}`,
          {
            league_id: metadata.league_id,
            platform: metadata.platform,
            privacy: metadata.privacy,
            espn_s2: metadata.espn_s2_cookie,
            swid: metadata.swid_cookie,
            seasons: metadata.seasons,
          },
          {
            headers: apiHeader,
          },
        );
        if (response.status === 200) {
          setOnboardingStatusId(response.data.data.execution_id);
          return true;
        }
      }
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        toast.error('Unexpected error onboarding league data.');
        return false;
      }
    } finally {
      setLoading(false);
    }
  };

  // Effect: Start polling once we have an ID
  useEffect(() => {
    if (!onboardingStatusId) return;

    void pollOnboardingStatus(); // initial fetch
    const interval = setInterval(() => {
      void pollOnboardingStatus();
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [onboardingStatusId, pollOnboardingStatus]);

  return (
    <div>
      {leagueOnboarded ? (
        <h1>Welcome to the home page!</h1>
      ) : (
        <div className="flex flex-col items-center gap-4 mt-8">
          <h1 className="text-center">Nothing to see here. Click the button below to onboard your league data.</h1>

          {/* Onboarding in progress */}
          {onboardingStatusId && onboardingStatus !== 'COMPLETED' ? (
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
              <p className="text-sm text-gray-600">Onboarding in progress... ({onboardingStatus || 'STARTED'})</p>
            </div>
          ) : (
            <Button
              onClick={() => {
                void onboardLeagueData();
              }}
              className="cursor-pointer"
              disabled={loading}
            >
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Submit
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

export default Home;
