import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import type { LeagueData } from './components/types/league_data';
import apiHeader from './components/utils/api_header';
import type { ApiResponse } from './components/types/api_response';

type LoginProps = {
  onLoginSuccess: (data: LeagueData) => void;
};

function Login({ onLoginSuccess }: LoginProps) {
  const [formData, setFormData] = useState({
    leagueId: '',
    platform: 'ESPN',
    privacy: '',
    oldestSeason: '',
    mostRecentSeason: '',
    swidCookie: '',
    espnS2Cookie: '',
  });
  const updateField = (field: keyof typeof formData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };
  const [showOnboardDialog, setShowOnboardDialog] = useState(false);
  const [loginFormErrors, setLoginFormErrors] = useState<{
    leagueId?: string;
    platform?: string;
    privacy?: string;
  }>({});

  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const seasons = useMemo(() => {
    const start = Number(formData.oldestSeason);
    const end = Number(formData.mostRecentSeason);
    if (!start || !end || isNaN(start) || isNaN(end)) return [];
    return Array.from({ length: end - start + 1 }, (_, i) => String(start + i));
  }, [formData.oldestSeason, formData.mostRecentSeason]);

  const checkLeagueExists = async () => {
    setLoading(true);
    try {
      const newErrors: typeof loginFormErrors = {};
      if (!formData.leagueId) newErrors.leagueId = 'Please enter your league ID';
      if (!formData.platform) newErrors.platform = 'Please select which platform your league is on';
      if (!formData.privacy) newErrors.privacy = 'Please indicate your league privacy settings';

      setLoginFormErrors(newErrors);

      // if no errors, proceed with API call
      if (Object.keys(newErrors).length === 0) {
        const response = await axios.get<ApiResponse>(
          `${import.meta.env.VITE_API_BASE_URL}/leagues/${formData.leagueId}?platform=${formData.platform}`,
          {
            headers: apiHeader,
          },
        );
        if (response.status === 200) {
          // Empty data object means league isn't onboarded yet
          if (!response.data?.data) {
            console.log('League does not exist');
            setShowOnboardDialog(true);
          } else {
            console.log('League found');
            onLoginSuccess({
              leagueId: formData.leagueId,
              platform: formData.platform,
            }); // Notify App.tsx of successful login
            void navigate('/home');
          }
        }
      } else {
        toast.error('Please fill in all form fields before clicking "Login".');
      }
    } catch {
      toast.error('An unexpected error occurred. Please try again, and if the error persists contact us.');
    } finally {
      setLoading(false);
    }
  };

  const checkValidLeagueInfo = async () => {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/leagues/validate`, {
        params: {
          league_id: formData.leagueId,
          platform: formData.platform,
          privacy: formData.privacy.toLowerCase(),
          season: formData.mostRecentSeason,
          swid_cookie: formData.swidCookie,
          espn_s2_cookie: formData.espnS2Cookie,
        },
        headers: apiHeader,
      });
      if (response.status === 200) {
        return true;
      }
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        toast.error('Invalid league information provided. Please double check all the form fields and try again.');
        setShowOnboardDialog(false);
        return false;
      }
    }
  };

  const onboardLeagueMetadata = async () => {
    setLoading(true);
    try {
      const validLeagueInfo = await checkValidLeagueInfo();
      if (!validLeagueInfo) {
        // No API call made to onboard league metadata if invalid info
        return;
      }
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/leagues/`,
        {
          league_id: formData.leagueId,
          platform: formData.platform,
          privacy: formData.privacy,
          espn_s2: formData.espnS2Cookie,
          swid: formData.swidCookie,
          seasons: seasons,
        },
        {
          headers: apiHeader,
        },
      );
      if (response.status === 201) {
        setShowOnboardDialog(false);
        toast.success('Successfully onboarded league!');
        onLoginSuccess({
          leagueId: formData.leagueId,
          platform: formData.platform,
        }); // Notify App.tsx of successful onboarding
        void navigate('/home');
      }
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        toast.error(
          'An error occurred while onboarding your league. Please try again, and if the error persists contact us.',
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <CardTitle>Provide your league information</CardTitle>
          <CardDescription>
            Enter your league ID, platform, privacy settings, and optional cookies (if your league is private).
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6">
          <div className="grid gap-3">
            <Label htmlFor="league-id">League ID</Label>
            <Input
              id="league-id"
              type="text"
              placeholder="12345"
              value={formData.leagueId}
              onChange={(e) => updateField('leagueId', e.target.value)}
            />
            {loginFormErrors.leagueId && <p className="text-red-500 text-sm">{loginFormErrors.leagueId}</p>}
          </div>
          <div className="grid gap-3">
            <Label htmlFor="platform">Platform</Label>
            <Select onValueChange={(value) => updateField('platform', value)} value={formData.platform}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a platform" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ESPN">ESPN</SelectItem>
              </SelectContent>
            </Select>
            {loginFormErrors.platform && <p className="text-red-500 text-sm">{loginFormErrors.platform}</p>}
          </div>
          <div className="grid gap-3">
            <Label htmlFor="privacy">League Privacy</Label>
            <Select onValueChange={(value) => updateField('privacy', value)} value={formData.privacy}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="League privacy setting" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Public">Public</SelectItem>
                <SelectItem value="Private">Private</SelectItem>
              </SelectContent>
            </Select>
            {loginFormErrors.privacy && <p className="text-red-500 text-sm">{loginFormErrors.privacy}</p>}
          </div>
        </CardContent>
        <CardFooter className="flex items-center justify-between">
          <Button
            onClick={() => {
              void checkLeagueExists();
            }}
            disabled={loading}
            className="cursor-pointer"
          >
            Login
          </Button>
        </CardFooter>
      </Card>
      <Dialog open={showOnboardDialog} onOpenChange={setShowOnboardDialog}>
        <DialogContent className="max-w-lg w-[90vw] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-center">Your league hasn't been onboarded yet</DialogTitle>
            <DialogDescription className="text-center">
              Fill in your fantasy league information to onboard your league. Instructions on how to find your ESPN
              cookies can be found{' '}
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
                <Input id="league-id" type="text" value={formData.leagueId} readOnly />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="league-platform">League Platform</Label>
                <Input id="league-platform" type="text" value={formData.platform} readOnly />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="league-privacy">League Privacy Setting</Label>
                <Input id="league-privacy" type="text" value={formData.privacy} readOnly />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="swid-cookie">First Season</Label>
                <Input
                  id="oldest-season"
                  type="text"
                  value={formData.oldestSeason}
                  onChange={(e) => updateField('oldestSeason', e.target.value)}
                />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="swid-cookie">Most Recent Season</Label>
                <Input
                  id="most-recent-season"
                  type="text"
                  value={formData.mostRecentSeason}
                  onChange={(e) => updateField('mostRecentSeason', e.target.value)}
                />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="swid-cookie">SWID Cookie</Label>
                <Input
                  id="swid-cookie"
                  type="text"
                  value={formData.swidCookie}
                  onChange={(e) => updateField('swidCookie', e.target.value)}
                />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="espn-s2-cookie">ESPN S2 Cookie</Label>
                <Input
                  id="espn-s2-cookie"
                  type="text"
                  value={formData.espnS2Cookie}
                  onChange={(e) => updateField('espnS2Cookie', e.target.value)}
                />
              </div>
            </CardContent>
            <CardFooter className="flex items-center justify-between">
              <Button
                onClick={() => {
                  void onboardLeagueMetadata();
                }}
                className="cursor-pointer"
                disabled={loading}
              >
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
