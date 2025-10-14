import { Info, Link, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ModeToggle } from '@/components/themes/mode_toggle';
import { queryClient } from '@/components/utils/query_client';
import type { HeaderProps } from '@/features/header/types';

const Header = ({ leagueData, onLogout }: HeaderProps) => {
  const handleLogout = () => {
    onLogout();
    queryClient.clear(); // clears all cached queries
  };

  return (
    <header className="flex items-center justify-center relative px-4 py-2 w-full">
      <h1 className="text-3xl font-bold mx-auto">Fantasy League Recap Dashboard</h1>
      <div className="absolute right-4 flex items-center gap-4">
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Info" className="cursor-pointer">
              <Info className="h-5 w-5" />
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>About</DialogTitle>
            </DialogHeader>
            <p>
              Welcome to Fantasy Football Recap, an app designed to provide fun charts and information about your
              fantasy league to easily answer questions like:
            </p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>Who has scored the most points ever in a week, and how many points did they score?</li>
              <li>What is my record against this team all-time?</li>
              <li>Who had the best draft this past season?</li>
            </ul>
          </DialogContent>
        </Dialog>
        <Button asChild variant="ghost" size="icon" aria-label="GitHub" className="cursor-pointer">
          <a
            href="https://github.com/amolrairikar/espn-fantasy-league-analytics"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Link className="h-5 w-5" />
          </a>
        </Button>
        {leagueData && (
          <Button variant="ghost" size="icon" aria-label="Logout" onClick={handleLogout} className="cursor-pointer">
            <LogOut className="h-5 w-5" />
          </Button>
        )}
        <ModeToggle />
      </div>
    </header>
  );
};

export default Header;
