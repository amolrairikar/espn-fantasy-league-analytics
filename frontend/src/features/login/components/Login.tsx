import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { LoadingButton } from '@/components/utils/loadingButton';
import { type FormValues, loginSchema } from '@/features/login/form_schema';
import {
  getLeagueMetadata,
  validateLeagueMetadata,
  postLeagueMetadata,
} from '@/api/league_metadata/api_calls';
import type { LoginProps } from '@/api/league_metadata/types';

function Login({ onLoginSuccess }: LoginProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showOnboardDialog, setShowOnboardDialog] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      leagueId: '',
      platform: 'ESPN',
      privacy: '',
      oldestSeason: '',
      mostRecentSeason: '',
      swidCookie: '',
      espnS2Cookie: '',
    },
  });

  // Watch form fields to refetch metadata if they change
  const leagueId = form.watch('leagueId');
  const platform = form.watch('platform');
  const privacy = form.watch('privacy');
  const watchedOldest = form.watch('oldestSeason');
  const watchedRecent = form.watch('mostRecentSeason');
  const swidCookie = form.watch('swidCookie');
  const espnS2Cookie = form.watch('espnS2Cookie');

  const seasons = useMemo(() => {
    const start = Number(watchedOldest);
    const end = Number(watchedRecent);
    // Validations for season range:
    // - Both start and end must be valid numbers
    // - Range cannot exceed 50 seasons
    // - Start cannot be after end
    if (!start || !end || isNaN(start) || isNaN(end) || end - start > 50 || start > end) return [];
    return Array.from({ length: end - start + 1 }, (_, i) => String(start + i));
  }, [watchedOldest, watchedRecent]);

  // Logic for initial Login click
  // Checks if the league has already been registered
  const checkLeagueExists = async () => {
    // Only trigger validation for the fields visible on the main card
    const isValid = await form.trigger(['leagueId', 'platform', 'privacy']);
    if (!isValid) return;

    setLoading(true);
    try {
      const metadata = await getLeagueMetadata(leagueId, platform);
      console.log(metadata);
      console.log(privacy);
      if (privacy.toLowerCase() != metadata.data.privacy) {
        toast.error('Incorrect league privacy setting selected.')
        return;
      }
      // If the league exists, store the league ID and platform in local storage and navigate to home page
      onLoginSuccess({ 
        leagueId: leagueId, 
        platform: platform, 
      });
      navigate('/home');
    } catch (error: any) {
      // A 404 error is valid and indicates that the league is not registered yet
      if (error.status === 404) {
        setShowOnboardDialog(true);
        toast.info('League not found. Please complete the registration form.');
        return;
      }
      else {
        console.log('Login error:', error);
        toast.error('An unexpected error occurred. Please try again and create a support ticket if the issue persists.');
      }
    } finally {
      setLoading(false);
    }
  };

  const onboardLeagueMetadata = async () => {
    // Validate all fields including cookies/seasons
    const isValid = await form.trigger();
    if (!isValid) return;

    setLoading(true);
    try {
      // Sends API request to validate form information with ESPN
      await validateLeagueMetadata(
        leagueId, 
        platform,
        privacy.toLowerCase(),
        watchedRecent!,
        espnS2Cookie!,
        swidCookie!,
      );

      // If successful, proceed to register the league
      const values = form.getValues();
      await postLeagueMetadata({
        league_id: values.leagueId,
        platform: values.platform,
        privacy: values.privacy.toLowerCase(),
        swid: values.swidCookie ?? "",
        espn_s2: values.espnS2Cookie ?? "",
        seasons: seasons,
      });

      // Notify user and navigate to home page
      toast.success('League successfully registered!');
      setShowOnboardDialog(false);
      onLoginSuccess({ leagueId: values.leagueId, platform: values.platform });
      navigate('/home');
    } catch (error: any) {
      if (error.status === 401) {
        toast.error('Invalid Credentials: The SWID or ESPN_S2 cookies are incorrect.');
      } else {
        toast.error('League validation failed. Please double check your information or raise a support ticket.');
      }
      return;
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form {...form}>
      <div className="space-y-6">
        <Card className="w-full max-w-md mx-auto">
          <CardHeader>
            <CardTitle>Provide your league information</CardTitle>
            <CardDescription>
              Enter your league ID, platform, and privacy setting. For ESPN, your league ID is in the URL like this:
              leagueId=12345. For Sleeper, you can find it in the URL like this: /leagues/12345.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <FormField
              control={form.control}
              name="leagueId"
              render={({ field }) => (
                <FormItem className="w-full">
                  <FormLabel>League ID</FormLabel>
                  <FormControl>
                    <Input placeholder="12345" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="platform"
              render={({ field }) => (
                <FormItem className="w-full">
                  <FormLabel>Platform</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select platform" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="ESPN">ESPN</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="privacy"
              render={({ field }) => (
                <FormItem className="w-full">
                  <FormLabel>League Privacy</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select privacy" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="Public">Public</SelectItem>
                      <SelectItem value="Private">Private</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
          <CardFooter>
            <LoadingButton 
              onClick={checkLeagueExists} 
              loading={loading}
            >
              Login
            </LoadingButton>
          </CardFooter>
        </Card>

        <Dialog open={showOnboardDialog} onOpenChange={setShowOnboardDialog}>
          <DialogContent className="max-w-lg w-[90vw] max-h-[90vh] flex flex-col">
            <DialogHeader>
              <DialogTitle>Register Your League</DialogTitle>
              <DialogDescription>
                We couldn't find your league. Please provide extra details to onboard it.
              </DialogDescription>
            </DialogHeader>

            <div className="flex-1 overflow-y-auto p-1 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="oldestSeason"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>First Season</FormLabel>
                      <FormControl>
                        <Input placeholder="2020" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="mostRecentSeason"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Most Recent Season</FormLabel>
                      <FormControl>
                        <Input placeholder="2024" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {privacy.toLowerCase() === 'private' ? (
                <>
                <FormField
                  control={form.control}
                  name="swidCookie"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>SWID Cookie</FormLabel>
                      <FormControl>
                        <Input type="password" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="espnS2Cookie"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>ESPN S2 Cookie</FormLabel>
                      <FormControl>
                        <Input type="password" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                </>
              ) : (
                <></>
              )}
          </div>

            <div className="pt-4 border-t">
              <LoadingButton
                onClick={onboardLeagueMetadata} 
                loading={loading}
              >
                Register League
              </LoadingButton>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Form>
  );
}

export default Login;