import { useState } from 'react';
import { Info, Link, LogOut, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { ModeToggle } from '@/components/themes/mode_toggle';
import MobileSidebar from '@/features/sidebar/components/mobileSidebar';
import { queryClient } from '@/components/utils/query_client';
import type { HeaderProps } from '@/features/header/types';

const Header = ({ leagueData, onLogout }: HeaderProps) => {
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    onLogout();
    queryClient.clear(); // clears all cached queries
    setOpen(false);
  };

  return (
    <header className="flex items-center justify-center relative px-4 py-2 w-full border-b">
      <h1 className="text-3xl font-bold mx-auto">Fantasy Recap</h1>

      {/* --- Desktop Icons --- */}
      <div className="absolute right-4 hidden md:flex items-center gap-4">
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Info">
              <Info className="h-5 w-5" />
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>About</DialogTitle>
            </DialogHeader>
            <p>
              Welcome to Fantasy Football Recap, an app designed to provide charts and stats for your fantasy league.
            </p>
          </DialogContent>
        </Dialog>

        <Button asChild variant="ghost" size="icon" aria-label="GitHub">
          <a
            href="https://github.com/amolrairikar/espn-fantasy-league-analytics"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Link className="h-5 w-5" />
          </a>
        </Button>

        {leagueData && (
          <Button variant="ghost" size="icon" aria-label="Logout" onClick={handleLogout}>
            <LogOut className="h-5 w-5" />
          </Button>
        )}
        <ModeToggle />
      </div>

      {/* --- Mobile Menu --- */}
      <div className="absolute right-4 flex md:hidden">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Menu">
              <Menu className="h-6 w-6" />
            </Button>
          </SheetTrigger>

          <SheetContent side="right" className="flex flex-col p-0">
            <MobileSidebar onNavigate={() => setOpen(false)} />

            <div className="border-t pt-4 flex flex-col space-y-4">
              <div className="border-t p-4 space-y-3">
                <Button asChild variant="ghost" className="justify-start cursor-pointer gap-2 w-full">
                  <a
                    href="https://github.com/amolrairikar/espn-fantasy-league-analytics"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Link className="h-5 w-5" />
                    GitHub
                  </a>
                </Button>
                {leagueData && (
                  <Button variant="ghost" className="justify-start gap-2 w-full" onClick={handleLogout}>
                    <LogOut className="h-5 w-5" />
                    Logout
                  </Button>
                )}
              </div>
              <div className="mt-auto border-t pt-4 px-4">
                <ModeToggle />
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  );
};

export default Header;
