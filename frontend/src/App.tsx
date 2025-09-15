import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import Login from './Login';
import Home from './Home';
import { useLocalStorage } from './hooks/useLocalStorage';
import { Toaster } from 'sonner';
import type { LeagueData } from './components/types/league_data';
import { ThemeProvider } from '@/components/themes/theme_provider';
import { ModeToggle } from './components/themes/mode_toggle';
import { Info, Link, LogOut } from 'lucide-react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';

function App() {
  return (
    <Router>
      <Toaster position="top-center" />
      <AppContent />
    </Router>
  );
}

function AppContent() {
  const [leagueData, setLeagueData] = useLocalStorage<LeagueData>('leagueData', null);
  const navigate = useNavigate();

  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <div>
        <div className="flex items-center justify-center relative px-4 py-2 w-full">
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
              <a href="https://github.com/amolrairikar/espn-fantasy-league-analytics" target="_blank" rel="noopener noreferrer">
                <Link className="h-5 w-5" />
              </a>
            </Button>
            {leagueData && (
              <Button
                variant="ghost"
                size="icon"
                aria-label="Logout"
                onClick={() => {
                  setLeagueData(null); // clear state
                  navigate('/login'); // redirect to login page
                }}
                className="cursor-pointer"
              >
                <LogOut className="h-5 w-5" />
              </Button>
            )}
            <ModeToggle />
          </div>
        </div>
        <Separator />
        <Routes>
          <Route
            path="/"
            element={leagueData ? <Navigate to="/home" /> : <Navigate to="/login" />}
          />
          <Route
            path="/login"
            element={
              <div className="mt-8">
                <Login onLoginSuccess={setLeagueData} />
              </div>
            }
          />
          <Route
            path="/home"
            element={<div className="mt-8">{leagueData ? <Home /> : <Navigate to="/login" />}</div>}
          />
        </Routes>
      </div>
    </ThemeProvider>
  );
}

export default App;
