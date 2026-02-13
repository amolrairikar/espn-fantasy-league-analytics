import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
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
import { LoadingButton } from '@/components/utils/formButton';
import { type LoginFormValues, loginFormSchema } from '@/features/login/login_form_schema';
import { getLeagueMetadata } from '@/api/league_metadata/api_calls';

export function LoginForm({ onLoginSuccess, onNotFound }: any) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  
  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginFormSchema),
    defaultValues: { leagueId: '', platform: 'ESPN' },
  });

  const onSubmit = async (data: Pick<LoginFormValues, 'leagueId' | 'platform'>) => {
    setLoading(true);
    try {
      const metadata = await getLeagueMetadata(data.leagueId, data.platform);
      console.log(metadata);
      // If the league exists, store the league ID and platform in local storage and navigate to home page
      onLoginSuccess({ leagueId: data.leagueId, platform: data.platform });
      navigate('/home');
    } catch (error: any) {
      // A 404 error is valid and indicates that the league is not registered yet
      // In this case, pass the league ID and platform to onNotFound and open onboarding dialog
      if (error.status === 404) {
        onNotFound(data.leagueId, data.platform);
      } else {
        toast.error('An unexpected error occurred.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <div className="space-y-6">
          <Card className="w-full max-w-md mx-auto">
            <CardHeader>
              <CardTitle>Provide your league information</CardTitle>
              <CardDescription>
                Enter your league ID, platform, and privacy setting. For ESPN, your league ID is in the URL like this:
                leagueId=12345.
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

            </CardContent>
            <CardFooter>
              <LoadingButton type="submit" loading={loading}>Login</LoadingButton>
            </CardFooter>
          </Card>
        </div>
      </form>
    </Form>
  );
}