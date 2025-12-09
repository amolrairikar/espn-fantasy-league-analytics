import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Info, Link, LogOut, Menu, Trash } from 'lucide-react';
import { useDeleteResource } from '@/components/hooks/genericDeleteRequest';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { ModeToggle } from '@/components/themes/mode_toggle';
import MobileSidebar from '@/features/sidebar/components/mobileSidebar';
import { LoadingButton } from '@/components/utils/loadingButton';
import { queryClient } from '@/components/utils/query_client';
import type { HeaderProps } from '@/features/header/types';

const Header = ({ leagueData, onLogout }: HeaderProps) => {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';
  const navigate = useNavigate();
  const [isAlertOpen, setIsAlertOpen] = useState(false);

  const handleLogout = () => {
    onLogout();
    queryClient.clear(); // clears all cached queries
    setOpen(false);
  };

  const deleteLeague = useDeleteResource('/delete_league', {
    onSuccess: (data) => {
      console.log('League deleted successfully:', data);
      queryClient.clear(); // clears all cached queries
      setIsAlertOpen(false);
      void navigate('/login');
    },
    onError: (err) => {
      console.error('Error deleting league:', err);
    },
  });

  const handleDelete = () => {
    console.log('Delete clicked');
    if (!leagueData) return;
    deleteLeague.mutate({
      league_id: leagueData.leagueId,
      platform: leagueData.platform,
    });
  };

  return (
    <header className="flex items-center justify-center relative px-4 py-2 w-full border-b">
      <h1 className="text-3xl font-bold mx-auto">Fantasy Recap</h1>

      {/* --- Desktop Icons --- */}
      <div className="absolute right-4 hidden md:flex items-center gap-4">
        <Dialog>
          <Tooltip>
            <TooltipTrigger asChild>
              <DialogTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Info">
                  <Info className="h-5 w-5" />
                </Button>
              </DialogTrigger>
            </TooltipTrigger>

            <TooltipContent>
              <p>Info</p>
            </TooltipContent>
          </Tooltip>

          <DialogContent>
            <DialogHeader>
              <DialogTitle>About</DialogTitle>
            </DialogHeader>
            <p>Welcome to Fantasy Football Recap...</p>
          </DialogContent>
        </Dialog>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button asChild variant="ghost" size="icon" aria-label="GitHub">
              <a
                href="https://github.com/amolrairikar/espn-fantasy-league-analytics"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Link className="h-5 w-5" />
              </a>
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>GitHub</p>
          </TooltipContent>
        </Tooltip>

        {!isLoginPage && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Logout" onClick={handleLogout}>
                <LogOut className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Logout</p>
            </TooltipContent>
          </Tooltip>
        )}

        {!isLoginPage && (
          <AlertDialog open={isAlertOpen} onOpenChange={setIsAlertOpen}>
            <Tooltip>
              <TooltipTrigger asChild>
                <AlertDialogTrigger asChild>
                  <Button variant="ghost" size="icon" aria-label="Delete League">
                    <Trash className="h-5 w-5" />
                  </Button>
                </AlertDialogTrigger>
              </TooltipTrigger>

              <TooltipContent>
                <p>Delete League</p>
              </TooltipContent>
            </Tooltip>

            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone...
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction asChild>
                  <LoadingButton onClick={handleDelete} loading={deleteLeague.isPending}>
                    Continue
                  </LoadingButton>
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}

        <ModeToggle />
      </div>

      {/* --- Mobile Menu --- */}
      {!isLoginPage && (
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
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="ghost" className="justify-start gap-2 w-full">
                        <Info className="h-5 w-5" />
                        Info
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>About</DialogTitle>
                      </DialogHeader>
                      <p>
                        Welcome to Fantasy Football Recap, an app designed to provide charts and stats for your fantasy
                        league.
                      </p>
                    </DialogContent>
                  </Dialog>
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
                  {!isLoginPage && (
                    <Button variant="ghost" className="justify-start gap-2 w-full" onClick={handleLogout}>
                      <LogOut className="h-5 w-5" />
                      Logout
                    </Button>
                  )}
                  {!isLoginPage && leagueData && (
                    <AlertDialog open={isAlertOpen} onOpenChange={setIsAlertOpen}>
                      <AlertDialogTrigger asChild>
                        <Button variant="ghost" className="justify-start gap-2 w-full">
                          <Trash className="h-5 w-5 text-red-600" />
                          <span className="text-red-600">Delete League</span>
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                          <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete your league data and you will
                            need to re-onboard again.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction asChild>
                            <LoadingButton onClick={handleDelete} loading={deleteLeague.isPending}>
                              Continue
                            </LoadingButton>
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  )}
                </div>
                <div className="mt-auto border-t pt-4 px-4">
                  <ModeToggle />
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      )}
    </header>
  );
};

export default Header;
