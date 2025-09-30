import { Info, Link, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import type { LeagueData } from './components/types/league_data';
import { ModeToggle } from './components/themes/mode_toggle';

interface HeaderProps {
  leagueData: LeagueData | null;
  onLogout: () => void;
}

const Header = ({ leagueData, onLogout }: HeaderProps) => (
  <header className="flex items-center justify-center relative px-4 py-2 w-full">
    <h1 className="text-3xl font-bold mx-auto">Fantasy League History Visualizer</h1>
    <div className="absolute right-4 flex items-center gap-4">
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Info" className="cursor-pointer">
            <Info className="h-5 w-5" />
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Info -- change later</DialogTitle>
          </DialogHeader>
          <p>Paragraph content -- change later</p>
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
        <Button variant="ghost" size="icon" aria-label="Logout" onClick={onLogout} className="cursor-pointer">
          <LogOut className="h-5 w-5" />
        </Button>
      )}
      <ModeToggle />
    </div>
  </header>
);

export default Header;
