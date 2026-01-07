import { Sheet, SheetContent } from '@/components/ui/sheet';
import type { GetMatchups } from '@/api/matchups/types';
import type { PlayerScoringDetails } from '@/features/standings/types';

interface MatchupSheetProps {
  matchup: GetMatchups['data'][number];
  open: boolean;
  onClose: () => void;
}

export function MatchupSheet({ matchup, open, onClose }: MatchupSheetProps) {
  if (!matchup) return null;

  const POSITION_ORDER = ['QB', 'RB', 'WR', 'TE', 'D/ST', 'K'];

  const groupPlayersByPosition = (players: PlayerScoringDetails[]) => {
    return players.reduce<Record<string, PlayerScoringDetails[]>>((acc, player) => {
      const pos = player.position || 'Other';
      if (!acc[pos]) acc[pos] = [];
      acc[pos].push(player);
      return acc;
    }, {});
  };

  const teamAStartersGrouped = groupPlayersByPosition(matchup.team_a_starting_players || []);
  const teamABenchGrouped = groupPlayersByPosition(matchup.team_a_bench_players || []);
  const teamBStartersGrouped = groupPlayersByPosition(matchup.team_b_starting_players || []);
  const teamBBenchGrouped = groupPlayersByPosition(matchup.team_b_bench_players || []);

  return (
    <Sheet open={open} onOpenChange={(val) => !val && onClose()}>
      <SheetContent className="w-full max-w-lg md:max-w-3xl flex flex-col bg-card text-foreground">
        <div className="mt-4 flex-1 overflow-y-auto px-4">
          {/* Team Names and Scores */}
          <div className="flex justify-between text-center font-semibold mb-4">
            {/* Team A */}
            <div className="w-1/2 flex flex-col items-center">
              <div className="flex items-center justify-center text-lg text-center min-h-12 leading-tight">
                <span className="line-clamp-2 wrap-break-word">{matchup.team_a_team_name}</span>
              </div>
              <div className="text-2xl mt-1">{matchup.team_a_score}</div>
              <div className="text-sm mt-4">Lineup Efficiency: {(matchup.team_a_efficiency*100).toFixed(2)}%</div>
            </div>

            {/* Team B */}
            <div className="w-1/2 flex flex-col items-center">
              <div className="flex items-center justify-center text-lg text-center min-h-12 leading-tight">
                <span className="line-clamp-2 wrap-break-word">{matchup.team_b_team_name}</span>
              </div>
              <div className="text-2xl mt-1">{matchup.team_b_score}</div>
              <div className="text-sm mt-4">Lineup Efficiency: {(matchup.team_b_efficiency*100).toFixed(2)}%</div>
            </div>
          </div>

          {/* Starters Header */}
          <div className="font-semibold mb-4 text-2xl">
            <div>Starters</div>
          </div>

          {/* Box Score Table (Starters) */}
          <div className="space-y-6">
            {POSITION_ORDER.map((pos) => {
              const teamAStartingPlayers = teamAStartersGrouped[pos] || [];
              const teamBStartingPlayers = teamBStartersGrouped[pos] || [];
              if (teamAStartingPlayers.length === 0 && teamBStartingPlayers.length === 0) return null;

              const maxPlayers = Math.max(teamAStartingPlayers.length, teamBStartingPlayers.length);
              return (
                <div key={pos}>
                  <h3 className="text-md font-semibold text-foreground mb-2">{pos}</h3>
                  <div className="grid grid-cols-2 gap-6">
                    {/* Team A */}
                    <div className="space-y-1">
                      {Array.from({ length: maxPlayers }).map((_, idx) => {
                        const player = teamAStartingPlayers[idx];
                        return (
                          <div
                            key={idx}
                            className="flex justify-between border-b border-border pb-1 text-sm min-h-6"
                          >
                            <span className="text-foreground">{player?.full_name || ''}</span>
                            <span className="font-mono text-muted-foreground">
                              {player ? Number(player.points_scored).toFixed(2) : ''}
                            </span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Team B */}
                    <div className="space-y-1 text-right">
                      {Array.from({ length: maxPlayers }).map((_, idx) => {
                        const player = teamBStartingPlayers[idx];
                        return (
                          <div
                            key={idx}
                            className="flex justify-between border-b border-border pb-1 text-sm min-h-6"
                          >
                            <span className="font-mono text-muted-foreground">
                              {player ? Number(player.points_scored).toFixed(2) : ''}
                            </span>
                            <span className="text-foreground">{player?.full_name || ''}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Bench Header (show only if there are bench players) */}
          {Object.values(teamABenchGrouped).some(players => players.length > 0) || Object.values(teamBBenchGrouped).some(players => players.length > 0) ? (
            <div className="font-semibold mb-4 text-2xl mt-6">
              <div>Bench</div>
            </div>
          ) : null}

          {/* Box Score Table (Bench) */}
          <div className="space-y-6">
            {POSITION_ORDER.map((pos) => {
              const teamABenchPlayers = teamABenchGrouped[pos] || [];
              const teamBBenchPlayers = teamBBenchGrouped[pos] || [];
              if (teamABenchPlayers.length === 0 && teamBBenchPlayers.length === 0) return null;

              const maxPlayers = Math.max(teamABenchPlayers.length, teamBBenchPlayers.length);
              return (
                <div key={pos}>
                  <h3 className="text-md font-semibold text-foreground mb-2">{pos}</h3>
                  <div className="grid grid-cols-2 gap-6">
                    {/* Team A */}
                    <div className="space-y-1">
                      {Array.from({ length: maxPlayers }).map((_, idx) => {
                        const player = teamABenchPlayers[idx];
                        return (
                          <div
                            key={idx}
                            className="flex justify-between border-b border-border pb-1 text-sm min-h-6"
                          >
                            <span className="text-foreground">{player?.full_name || ''}</span>
                            <span className="font-mono text-muted-foreground">
                              {player ? Number(player.points_scored).toFixed(2) : ''}
                            </span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Team B */}
                    <div className="space-y-1 text-right">
                      {Array.from({ length: maxPlayers }).map((_, idx) => {
                        const player = teamBBenchPlayers[idx];
                        return (
                          <div
                            key={idx}
                            className="flex justify-between border-b border-border pb-1 text-sm min-h-6"
                          >
                            <span className="font-mono text-muted-foreground">
                              {player ? Number(player.points_scored).toFixed(2) : ''}
                            </span>
                            <span className="text-foreground">{player?.full_name || ''}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      </SheetContent>
    </Sheet>
  );
}
