import { toast } from 'sonner';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { usePostResource } from '@/components/hooks/genericPostRequest';
import { LoadingButton } from '@/components/utils/loadingButton';
import type { GetLeagueMetadata } from '@/features/login/types';
import type { ValidateLeagueReponse } from '@/features/login/types';
import type { PostLeagueMetadataPayload, PostLeagueMetadataResponse } from '@/features/login/types';
import type { LeagueData } from '@/features/login/types';

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
    firstSeason?: string;
    lastSeason?: string;
    swidCookie?: string;
    espnS2Cookie?: string;
  }>({});

  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const seasons = useMemo(() => {
    const start = Number(formData.oldestSeason);
    const end = Number(formData.mostRecentSeason);
    if (!start || !end || isNaN(start) || isNaN(end)) return [];
    return Array.from({ length: end - start + 1 }, (_, i) => String(start + i));
  }, [formData.oldestSeason, formData.mostRecentSeason]);

  const { refetch: refetchLeagueMetadata } = useGetResource<GetLeagueMetadata>(`/leagues/${formData.leagueId}`, {
    platform: formData.platform,
  });
  const { refetch: refetchLeagueValid } = useGetResource<ValidateLeagueReponse>(`/leagues/validate`, {
    league_id: formData.leagueId,
    platform: formData.platform,
    privacy: formData.privacy.toLowerCase(),
    season: formData.mostRecentSeason,
    swid_cookie: formData.swidCookie,
    espn_s2_cookie: formData.espnS2Cookie,
  });
  const { mutateAsync } = usePostResource<PostLeagueMetadataPayload, PostLeagueMetadataResponse>('/leagues/');

  const checkLeagueExists = async () => {
    setLoading(true);
    try {
      const newErrors: typeof loginFormErrors = {};
      if (!formData.leagueId) newErrors.leagueId = 'Please enter your league ID';
      if (!formData.platform) newErrors.platform = 'Please select which platform your league is on';
      if (!formData.privacy) newErrors.privacy = 'Please indicate your league privacy settings';
      setLoginFormErrors(newErrors);

      // if no missing fields, proceed with API call
      if (Object.keys(newErrors).length === 0) {
        const result = await refetchLeagueMetadata();
        if (result.error) {
          const err = result.error as Error & { status?: number };
          if (err.status === 404) {
            setShowOnboardDialog(true);
            toast.error('League not found, please sign up your league using the form.');
            return;
          } else {
            console.log(`An unexpected error occurred: ${err.message}`);
            toast.error('An unexpected error occurred. Please try again.');
            return;
          }
        }
        console.log('League metadata:', result.data);
        onLoginSuccess({ leagueId: formData.leagueId, platform: formData.platform });
        void navigate('/home');
      } else {
        toast.error('Please fill in all form fields before clicking "Login".');
      }
    } catch (error) {
      console.error('Error checking league existence:', error);
      toast.error('An error occurred while checking the league. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const onboardLeagueMetadata = async () => {
    setLoading(true);
    try {
      const newErrors: typeof loginFormErrors = {};
      if (!formData.leagueId) newErrors.leagueId = 'Please enter your league ID';
      if (!formData.platform) newErrors.platform = 'Please select which platform your league is on';
      if (!formData.privacy) newErrors.privacy = 'Please indicate your league privacy settings';
      if (!formData.oldestSeason) newErrors.firstSeason = 'Please enter the season your league started in';
      if (!formData.mostRecentSeason)
        newErrors.lastSeason = 'Please enter the most recent season your league was active for';
      if (!formData.swidCookie) newErrors.swidCookie = 'Please enter your SWID cookie';
      if (!formData.espnS2Cookie) newErrors.espnS2Cookie = 'Please enter your ESPN S2 cookie';
      setLoginFormErrors(newErrors);

      // if no missing fields, proceed with API call(s)
      if (Object.keys(newErrors).length === 0) {
        const validLeagueResult = await refetchLeagueValid();
        if (validLeagueResult.status === 'success') {
          console.log('Valid league information entered');
          const payload = {
            league_id: formData.leagueId,
            platform: formData.platform,
            privacy: formData.privacy.toLowerCase(),
            swid: formData.swidCookie,
            espn_s2: formData.espnS2Cookie,
            seasons: seasons,
          };
          try {
            const result = await mutateAsync(payload);
            if (result.status === 'success') {
              toast.success('League successfully reigstered!');
              setShowOnboardDialog(false);
              onLoginSuccess({ leagueId: formData.leagueId, platform: formData.platform });
              void navigate('/home');
            }
          } catch (error) {
            console.error('Error registering league:', error);
            toast.error('An error occurred while registering the league. Please try again.');
            return;
          }
        }
      } else {
        toast.error('Please fill in all form fields before clicking "Register".');
      }
    } catch (error) {
      console.error('Error validating league:', error);
      toast.error(
        'An error occurred while validating the league information you entered. Please check your inputs and try again.',
      );
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
            Enter your league ID, platform, and privacy setting. For ESPN, your league ID is in the URL like this:
            leagueId=12345. For Sleeper, you can find it in the URL like this: /leagues/12345.
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
          <LoadingButton onClick={() => void checkLeagueExists()} loading={loading}>
            Login
          </LoadingButton>
        </CardFooter>
      </Card>
      <Dialog open={showOnboardDialog} onOpenChange={setShowOnboardDialog}>
        <DialogContent className="max-w-lg w-[90vw] max-h-[90vh] flex flex-col">
          <DialogHeader className="shrink-0">
            <DialogTitle className="text-center">Your league hasn't been registered yet</DialogTitle>
            <DialogDescription className="text-center">
              Fill in your fantasy league information to register your league. Instructions on how to find your ESPN
              cookies can be found{' '}
              <a href="https://www.espn.com" target="_blank" className="text-blue-600">
                here
              </a>
              .
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto p-4">
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
                  {loginFormErrors.firstSeason && <p className="text-red-500 text-sm">{loginFormErrors.firstSeason}</p>}
                </div>
                <div className="grid gap-3">
                  <Label htmlFor="swid-cookie">Most Recent Season</Label>
                  <Input
                    id="most-recent-season"
                    type="text"
                    value={formData.mostRecentSeason}
                    onChange={(e) => updateField('mostRecentSeason', e.target.value)}
                  />
                  {loginFormErrors.lastSeason && <p className="text-red-500 text-sm">{loginFormErrors.lastSeason}</p>}
                </div>
                <div className="grid gap-3">
                  <Label htmlFor="swid-cookie">SWID Cookie</Label>
                  <Input
                    id="swid-cookie"
                    type="text"
                    value={formData.swidCookie}
                    onChange={(e) => updateField('swidCookie', e.target.value)}
                  />
                  {loginFormErrors.swidCookie && <p className="text-red-500 text-sm">{loginFormErrors.swidCookie}</p>}
                </div>
                <div className="grid gap-3">
                  <Label htmlFor="espn-s2-cookie">ESPN S2 Cookie</Label>
                  <Input
                    id="espn-s2-cookie"
                    type="text"
                    value={formData.espnS2Cookie}
                    onChange={(e) => updateField('espnS2Cookie', e.target.value)}
                  />
                  {loginFormErrors.espnS2Cookie && (
                    <p className="text-red-500 text-sm">{loginFormErrors.espnS2Cookie}</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
          <div className="shrink-0 p-4 border-t">
            <LoadingButton onClick={() => void onboardLeagueMetadata()} loading={loading}>
              Register
            </LoadingButton>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default Login;
