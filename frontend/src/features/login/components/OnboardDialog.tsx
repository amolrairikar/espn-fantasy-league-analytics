import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, useWatch } from 'react-hook-form';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { LoadingButton } from '@/components/utils/formButton';
import { type OnboardingFormValues, onboardingSchema } from '@/features/login/onboarding_form_schema';
import { calculateSeasonRange } from '@/features/login/utils';
import {
  validateLeagueMetadata,
  postLeagueMetadata,
} from '@/api/league_metadata/api_calls';

export function OnboardDialog({ open, onOpenChange, initialData, onLoginSuccess }: any) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const form = useForm<OnboardingFormValues>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      ...initialData,
      oldestSeason: '',
      mostRecentSeason: '',
      swidCookie: '',
      espnS2Cookie: '',
    },
  });

  useEffect(() => {
    if (open) {
      form.reset({
        leagueId: initialData.leagueId,
        platform: initialData.platform,
        oldestSeason: '',
        mostRecentSeason: '',
        swidCookie: '',
        espnS2Cookie: '',
      });
    }
  }, [open, initialData, form]);

  const watchedSeasons = useWatch({
    control: form.control,
    name: ['oldestSeason', 'mostRecentSeason']
  });

  const seasons = useMemo(() => {
    const [oldest, recent] = watchedSeasons;
    return calculateSeasonRange(oldest, recent);
  }, [watchedSeasons]);


  const onRegisterSubmit = async (data: OnboardingFormValues) => {
    // Manual check for seasons array because this is derived data not in the schema
    if (!seasons || seasons.length === 0) {
      toast.error("Please provide a valid season range.");
      return;
    }

    const mostRecentSeason = seasons[seasons.length - 1];
    setLoading(true);

    try {
      await validateLeagueMetadata(
        data.leagueId,
        data.platform,
        mostRecentSeason,
        data.espnS2Cookie,
        data.swidCookie
      );

      // If successful, proceed to register the league
      await postLeagueMetadata({
        league_id: data.leagueId,
        platform: data.platform,
        swid: data.swidCookie,
        espn_s2: data.espnS2Cookie,
        seasons: seasons,
      });

      // Notify user and navigate to home page
      toast.success('League successfully registered!');
      onLoginSuccess({ leagueId: data.leagueId, platform: data.platform });
      navigate('/home');
    } catch (error: any) {
      toast.error('League validation failed. Please check your info or raise a support ticket.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onRegisterSubmit)} className="space-y-4">
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
              </div>
            </div>

            <div className="pt-4 border-t">
              <LoadingButton type="submit" loading={loading}>
                Register League
              </LoadingButton>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}