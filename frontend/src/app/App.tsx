import { Suspense, lazy } from 'react';
import { Toaster } from 'sonner';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useMediaQuery } from '@custom-react-hooks/use-media-query';
import ApiErrorBanner from '@/components/utils/apiErrorBanner';
import type { LeagueData } from '@/components/types/league_data';
import { ThemeProvider } from '@/components/themes/theme_provider';
import { Separator } from '@/components/ui/separator';
import { SidebarProvider } from '@/components/ui/sidebar';
import Header from '@/features/header/components/Header';
import DesktopSidebar from '@/features/sidebar/components/desktopSidebar';
const Login = lazy(() => import('@/features/login/components/Login'));
const Home = lazy(() => import('@/features/home/components/Home'));
const Scores = lazy(() => import('@/features/scores/components/Scores'));
const Standings = lazy(() => import('@/features/standings/components/Standings'));
const Draft = lazy(() => import('@/features/draft/components/Draft'));
import { useLocalStorage } from '@/components/hooks/useLocalStorage';

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
      <ApiErrorBanner>
        <Toaster position="top-center" />
        <AppContent />
      </ApiErrorBanner>
    </Router>
  );
}

function AppContent() {
  const [leagueData, setLeagueData] = useLocalStorage<LeagueData | null>('leagueData', null);
  const navigate = useNavigate();
  const location = useLocation();

  const isMobile = useMediaQuery('(max-width: 768px)');
  const showSidebar = !isMobile && location.pathname !== '/login';

  const handleLogout = () => {
    setLeagueData(null);
    void navigate('/login');
  };

  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <SidebarProvider>
        <div className="flex h-screen w-screen">
          {/* Sidebar only when logged in */}
          {showSidebar && <DesktopSidebar />}
          <div className="flex flex-col flex-1 overflow-hidden">
            <Header leagueData={leagueData} onLogout={handleLogout} />
            <Separator />

            {/* Main content area */}
            <main
              className={
                showSidebar
                  ? 'flex-1 mt-8 container mx-auto px-4 overflow-auto'
                  : 'flex-1 mt-4 w-full overflow-auto bg-background'
              }
            >
              <Suspense fallback={<div className="text-center">Loading...</div>}>
                <Routes>
                  <Route path="/" element={<Navigate to={leagueData ? '/home' : '/login'} />} />

                  {/* Wrap Login page to maintain normal width */}
                  <Route
                    path="/login"
                    element={
                      <div className="w-full max-w-2xl sm:max-w-3xl md:max-w-4xl px-6 mt-4 mx-auto">
                        <Login onLoginSuccess={setLeagueData} />
                      </div>
                    }
                  />

                  {/* Protected routes wrapper */}
                  <Route element={<ProtectedRoute isAllowed={!!leagueData} redirectTo="/login" />}>
                    <Route path="/home" element={<Home />} />
                    <Route path="/scores" element={<Scores />} />
                    <Route path="/standings" element={<Standings />} />
                    <Route path="/draft" element={<Draft />} />
                  </Route>
                </Routes>
              </Suspense>
            </main>
          </div>
        </div>
      </SidebarProvider>
    </ThemeProvider>
  );
}

export default App;
