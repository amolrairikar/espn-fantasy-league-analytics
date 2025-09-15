import axios from 'axios';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { LeagueData } from './components/types/league_data';

type LoginProps = {
  onLoginSuccess: (data: LeagueData) => void;
};

function Login({ onLoginSuccess }: LoginProps) {
  const [leagueId, setLeagueId] = useState<string>('');
  const [platform, setPlatform] = useState<string>('ESPN');
  const [privacy, setPrivacy] = useState<string>('');
  const [mostRecentSeason, setMostRecentSeason] = useState<string>('');
  const [swidCookie, setSwidCookie] = useState<string>('');
  const [espnS2Cookie, setEspnS2Cookie] = useState<string>('');
  const [showOnboardDialog, setShowOnboardDialog] = useState(false);
  const [loginFormErrors, setLoginFormErrors] = useState<{
    leagueId?: string;
    platform?: string;
    privacy?: string;
  }>({});

  const navigate = useNavigate();

  const checkLeagueExists = async () => {
    const newErrors: typeof loginFormErrors = {};
    if (!leagueId) newErrors.leagueId = 'Please enter your league ID';
    if (!platform) newErrors.platform = 'Please select which platform your league is on';
    if (!privacy) newErrors.privacy = 'Please indicate your league privacy settings';

    setLoginFormErrors(newErrors);

    // if no errors, proceed with API call
    if (Object.keys(newErrors).length === 0) {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_BASE_URL}/leagues/${leagueId}?platform=${platform}`,
          {
            headers: {
              'x-api-Key': import.meta.env.VITE_API_KEY,
            },
          },
        );
        if (response.status === 200) {
          if (!response.data?.data) {
            // No data object, open onboard dialog
            console.log('No data returned');
            toast.warning('League not onboarded, please onboard your league first.');
            setShowOnboardDialog(true);
          } else {
            console.log('League found');
            onLoginSuccess({
              leagueId,
              platform,
              privacy,
              swidCookie,
              espnS2Cookie,
            }); // Notify App.tsx of successful login
            navigate('/home');
          }
        }
      } catch (error: any) {
        if (axios.isAxiosError(error) && error.response) {
          toast.error(
            'An unexpected error occurred. Please try again, and if the error persists contact us.',
          );
        }
      }
    }
  };

  const checkValidLeagueInfo = async () => {
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/leagues/validate/${mostRecentSeason}`,
        {
          league_id: leagueId,
          platform: platform,
          privacy: privacy,
          espn_s2: espnS2Cookie,
          swid: swidCookie,
        },
        {
          headers: {
            'x-api-Key': import.meta.env.VITE_API_KEY,
          },
        },
      );
      if (response.status === 200) {
        return true;
      }
    } catch (error: any) {
      if (axios.isAxiosError(error) && error.response) {
        toast.error(
          'Invalid league information provided. Please double check all the form fields and try again.',
        );
        setShowOnboardDialog(false);
        return false;
      }
    }
  };

  const onboardLeague = async () => {
    const validLeagueInfo = await checkValidLeagueInfo();
    if (!validLeagueInfo) {
      return;
    }
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/leagues/`,
        {
          league_id: leagueId,
          platform: platform,
          privacy: privacy,
          espn_s2: espnS2Cookie,
          swid: swidCookie,
        },
        {
          headers: {
            'x-api-Key': import.meta.env.VITE_API_KEY,
          },
        },
      );
      if (response.status === 201) {
        setShowOnboardDialog(false);
        onLoginSuccess({
          leagueId,
          platform,
          privacy,
          swidCookie,
          espnS2Cookie,
        }); // Notify App.tsx of successful onboarding
        navigate('/home');
      }
    } catch (error: any) {
      if (axios.isAxiosError(error) && error.response) {
        toast.error(
          'An error occurred while onboarding your league. Please try again, and if the error persists contact us.',
        );
      }
    }
  };

  return (
    <div>
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <CardTitle>Provide your league information</CardTitle>
          <CardDescription>
            Enter your league ID, platform, privacy settings, and optional cookies (if your league
            is private).
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6">
          <div className="grid gap-3">
            <Label htmlFor="league-id">League ID</Label>
            <Input
              id="league-id"
              type="text"
              placeholder="12345"
              value={leagueId}
              onChange={(e) => setLeagueId(e.target.value)}
            />
            {loginFormErrors.leagueId && (
              <p className="text-red-500 text-sm">{loginFormErrors.leagueId}</p>
            )}
          </div>
          <div className="grid gap-3">
            <Label htmlFor="platform">Platform</Label>
            <Select onValueChange={(value) => setPlatform(value)} value={platform}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a platform" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ESPN">ESPN</SelectItem>
              </SelectContent>
            </Select>
            {loginFormErrors.platform && (
              <p className="text-red-500 text-sm">{loginFormErrors.platform}</p>
            )}
          </div>
          <div className="grid gap-3">
            <Label htmlFor="privacy">League Privacy</Label>
            <Select onValueChange={(value) => setPrivacy(value)} value={privacy}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="League privacy setting" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Public">Public</SelectItem>
                <SelectItem value="Private">Private</SelectItem>
              </SelectContent>
            </Select>
            {loginFormErrors.privacy && (
              <p className="text-red-500 text-sm">{loginFormErrors.privacy}</p>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex items-center justify-between">
          <Button onClick={checkLeagueExists} className="cursor-pointer">
            Login
          </Button>
        </CardFooter>
      </Card>
      <Dialog open={showOnboardDialog} onOpenChange={setShowOnboardDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>League Information</DialogTitle>
            <DialogDescription>
              Fill in your fantasy league information to onboard your league. Instructions on how to
              find your ESPN cookies can be found{' '}
              <a href="https://www.espn.com" target="_blank" className="text-blue-600">
                here
              </a>
              .
            </DialogDescription>
          </DialogHeader>
          <Card className="w-full max-w-md mx-auto">
            <CardContent className="grid gap-6">
              <div className="grid gap-3">
                <Label htmlFor="league-id">League ID</Label>
                <Input id="league-id" type="text" value={leagueId} readOnly />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="league-platform">League Platform</Label>
                <Input id="league-platform" type="text" value={platform} readOnly />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="league-privacy">League Privacy Setting</Label>
                <Input id="league-privacy" type="text" value={privacy} readOnly />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="swid-cookie">Most Recent Season</Label>
                <Input
                  id="most-recent-season"
                  type="text"
                  value={mostRecentSeason}
                  onChange={(e) => setMostRecentSeason(e.target.value)}
                />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="swid-cookie">SWID Cookie</Label>
                <Input
                  id="swid-cookie"
                  type="text"
                  value={swidCookie}
                  onChange={(e) => setSwidCookie(e.target.value)}
                />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="espn-s2-cookie">ESPN S2 Cookie</Label>
                <Input
                  id="espn-s2-cookie"
                  type="text"
                  value={espnS2Cookie}
                  onChange={(e) => setEspnS2Cookie(e.target.value)}
                />
              </div>
            </CardContent>
            <CardFooter className="flex items-center justify-between">
              <Button onClick={onboardLeague} className="cursor-pointer">
                Submit
              </Button>
            </CardFooter>
          </Card>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default Login;
