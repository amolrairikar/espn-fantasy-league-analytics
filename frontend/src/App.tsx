import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from "@/components/ui/dialog"
import { Separator } from "@/components/ui/separator"
import Login from "./Login"
import Home from "./Home"
import { Toaster } from "sonner"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom";
import type { LeagueData } from "./components/types/league_data"
import { ThemeProvider } from "@/components/themes/theme_provider"
import { ModeToggle } from "./components/themes/mode_toggle"
import { Info, Link, LogOut } from "lucide-react"
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom"

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

function AppContent() {

  const [leagueData, setLeagueData] = useState<LeagueData | null>(() => {
    const stored = localStorage.getItem("leagueData");
    return stored ? JSON.parse(stored) : null;
  });

  const navigate = useNavigate();

  // Keep localStorage in sync
  useEffect(() => {
    if (leagueData) {
      localStorage.setItem("leagueData", JSON.stringify(leagueData));
    } else {
      localStorage.removeItem("leagueData");
    }
  }, [leagueData]);

  return (
    <div>
      <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
        <Toaster position="top-center" />
          <div className="relative flex items-center justify-center px-4 py-2">
            {/* Centered title */}
            <h1 className="text-3xl font-bold">Fantasy League History Visualizer</h1>

            {/* Right-side icons */}
            <div className="absolute right-4 flex items-center gap-4">
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="icon" aria-label="Info" className="cursor-pointer">
                    <Info className="h-5 w-5" />
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>
                      Info -- change later
                    </DialogTitle>
                  </DialogHeader>
                  <p>Paragraph content -- change later</p>
                </DialogContent>
              </Dialog>
              <a
                href="https://github.com/amolrairikar/espn-fantasy-league-analytics"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="ghost" size="icon" aria-label="GitHub" className="cursor-pointer">
                  <Link className="h-5 w-5" />
                </Button>
              </a>
              {leagueData && (
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Logout"
                  onClick={() => {
                    setLeagueData(null); // clear state
                    navigate("/login");  // redirect to login page
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
              element={
                leagueData ? <Navigate to="/home" /> : <Navigate to="/login" />
              }
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
              element={
                leagueData ? <Home /> : <Navigate to="/login" />
              }
            />
          </Routes>
      </ThemeProvider>
    </div>
  )
}

export default App
