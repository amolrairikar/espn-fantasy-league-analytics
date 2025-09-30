import { Suspense, lazy } from 'react';
import { Toaster } from 'sonner';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, Outlet } from 'react-router-dom';
import type { LeagueData } from './components/types/league_data';
import { ThemeProvider } from '@/components/themes/theme_provider';
import { Separator } from '@/components/ui/separator';
import Header from './Header';
const Login = lazy(() => import('./Login'));
const Home = lazy(() => import('./Home'));
import { useLocalStorage } from './hooks/useLocalStorage';

interface ProtectedRouteProps {
  isAllowed: boolean;
  redirectTo: string;
}

const ProtectedRoute = ({ isAllowed, redirectTo }: ProtectedRouteProps) => {
  return isAllowed ? <Outlet /> : <Navigate to={redirectTo} />;
};

function App() {
  return (
    <Router>
      <Toaster position="top-center" />
      <AppContent />
    </Router>
  );
}

function AppContent() {
  const [leagueData, setLeagueData] = useLocalStorage<LeagueData | null>('leagueData', null);
  const navigate = useNavigate();

  const handleLogout = () => {
    setLeagueData(null);
    void navigate('/login');
  };

  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <div>
        <Header leagueData={leagueData} onLogout={handleLogout} />
        <Separator />
        <main className="mt-8 container mx-auto px-4">
          <Suspense fallback={<div className="text-center">Loading...</div>}>
            <Routes>
              <Route path="/" element={<Navigate to={leagueData ? '/home' : '/login'} />} />
              <Route path="/login" element={<Login onLoginSuccess={setLeagueData} />} />

              {/* Protected routes wrapper */}
              <Route element={<ProtectedRoute isAllowed={!!leagueData} redirectTo="/login" />}>
                <Route path="/home" element={<Home />} />
                {/* Add future protected pages here */}
              </Route>
            </Routes>
          </Suspense>
        </main>
      </div>
    </ThemeProvider>
  );
}

export default App;
