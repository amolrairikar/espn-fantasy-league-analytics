import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';

// UI Components
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
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ProgressDialog } from "@/components/utils/progressDialog";

// Logic & API
import { type OnboardingFormValues, onboardingSchema } from '@/features/login/onboarding_form_schema';
import { validateLeagueMetadata } from '@/api/league_metadata/api_calls';
import { postLeagueOnboarding } from '@/api/onboarding/api_calls';
import { getLeagueDatabase } from '@/api/database/api_calls';
import type { PostLeagueOnboardingPayload } from '@/api/onboarding/types';
import { calculateSeasonRange } from '@/features/login/utils';

export default function Login() {
  const navigate = useNavigate();

  const [isProgressOpen, setIsProgressOpen] = useState(false);
  const [progressText, setProgressText] = useState("");
  const [estimatedSeconds, setEstimatedSeconds] = useState(5);
  const [apiCallsDone, setApiCallsDone] = useState(false);
  
  const form = useForm<OnboardingFormValues>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: { 
      leagueId: '', 
      platform: 'ESPN',
      oldestSeason: '',
      mostRecentSeason: '',
      swidCookie: '',
      espnS2Cookie: ''
    },
  });

  const onSubmit = async (data: OnboardingFormValues) => {
    try {
      setApiCallsDone(false);
      setProgressText("Validating league credentials...");
      setEstimatedSeconds(20); 
      setIsProgressOpen(true);

      // Validate user's credentials
      await validateLeagueMetadata(
        data.leagueId,
        data.platform,
        data.mostRecentSeason,
        data.espnS2Cookie,
        data.swidCookie
      );

      // Trigger onboarding
      setProgressText("Credentials verified! Onboarding league...");
      const onboardingPayload: PostLeagueOnboardingPayload = {
        league_id: data.leagueId,
        platform: data.platform,
        espn_s2: data.espnS2Cookie,
        swid: data.swidCookie,
        seasons: calculateSeasonRange(data.oldestSeason, data.mostRecentSeason)
      };
      await postLeagueOnboarding(onboardingPayload);
      setProgressText("Fetching data from ESPN...");

      // Fetch league database
      const { data: { url: dbUrl, version: dbVersion } } = await getLeagueDatabase(data.leagueId);
      setProgressText("Retrieving league database...");
      localStorage.setItem('league_id', data.leagueId);
      localStorage.setItem('db_url', dbUrl);
      localStorage.setItem('db_version', dbVersion);

      // Complete onboarding
      setApiCallsDone(true); 
      navigate('/home');
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.detail || 'An unexpected error occurred during onboarding.');
    } finally {
      setIsProgressOpen(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-vh-100 p-4">
      <ProgressDialog
        isOpen={isProgressOpen}
        text={progressText}
        maxTimeInSeconds={estimatedSeconds}
        title="Setting Up Your League"
        isCompleting={apiCallsDone}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="w-full">
          <div className="space-y-6">
            <Card className="w-full max-w-md mx-auto">
              <CardHeader>
                <CardTitle>Provide your league information</CardTitle>
                <CardDescription>
                  Enter your league ID and credentials. For ESPN, your league ID is in the URL (e.g., leagueId=12345).
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-6">
                
                {/* League ID and Platform */}
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="leagueId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>League ID</FormLabel>
                        <FormControl>
                          <Input placeholder="12345" {...field} className="w-full" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="platform"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Platform</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select" />
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
                </div>

                {/* Season Range */}
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

                {/* Cookies */}
                <FormField
                  control={form.control}
                  name="swidCookie"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>SWID Cookie</FormLabel>
                      <FormControl>
                        <Input type="password" spellCheck="false" {...field} />
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
                        <Input type="password" spellCheck="false" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

              </CardContent>
              <CardFooter>
                <Button type="submit" className="w-full">Login & Onboard</Button>
              </CardFooter>
            </Card>
          </div>
        </form>
      </Form>
    </div>
  );
}