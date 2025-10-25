import { Sheet, SheetContent } from '@/components/ui/sheet';
import type { GetMatchups, PlayerScoring } from '@/features/standings/types';

interface MatchupSheetProps {
  matchup: GetMatchups['data'][number];
  open: boolean;
  onClose: () => void;
}

export function MatchupSheet({ matchup, open, onClose }: MatchupSheetProps) {
  if (!matchup) return null;

  const POSITION_ORDER = ['QB', 'RB', 'WR', 'TE', 'D/ST', 'K'];

  const groupPlayersByPosition = (players: PlayerScoring[]) => {
    return players.reduce<Record<string, PlayerScoring[]>>((acc, player) => {
      const pos = player.position || 'Other';
      if (!acc[pos]) acc[pos] = [];
      acc[pos].push(player);
      return acc;
    }, {});
  };

  const teamAGrouped = groupPlayersByPosition(matchup.team_a_players || []);
  const teamBGrouped = groupPlayersByPosition(matchup.team_b_players || []);

  return (
    <Sheet open={open} onOpenChange={(val) => !val && onClose()}>
      <SheetContent className="w-full max-w-lg md:max-w-3xl flex flex-col bg-card text-foreground">
        <div className="mt-4 flex-1 overflow-y-auto px-4">
          {/* Team Names and Scores */}
          <div className="flex justify-between text-center font-semibold mb-4">
            {/* Team A */}
            <div className="w-1/2 flex flex-col items-center">
              <div className="flex items-center justify-center text-lg text-center min-h-[3rem] leading-tight">
                <span className="line-clamp-2 break-words">{matchup.team_a_team_name}</span>
              </div>
              <div className="text-2xl mt-1">{matchup.team_a_score}</div>
            </div>

            {/* Team B */}
            <div className="w-1/2 flex flex-col items-center">
              <div className="flex items-center justify-center text-lg text-center min-h-[3rem] leading-tight">
                <span className="line-clamp-2 break-words">{matchup.team_b_team_name}</span>
              </div>
              <div className="text-2xl mt-1">{matchup.team_b_score}</div>
            </div>
          </div>

          {/* Box Score Table */}
          <div className="space-y-6">
            {POSITION_ORDER.map((pos) => {
              const teamAPlayers = teamAGrouped[pos] || [];
              const teamBPlayers = teamBGrouped[pos] || [];
              if (teamAPlayers.length === 0 && teamBPlayers.length === 0) return null;

              const maxPlayers = Math.max(teamAPlayers.length, teamBPlayers.length);

              return (
                <div key={pos}>
                  <h3 className="text-md font-semibold text-foreground mb-2">{pos}</h3>
                  <div className="grid grid-cols-2 gap-6">
                    {/* Team A */}
                    <div className="space-y-1">
                      {Array.from({ length: maxPlayers }).map((_, idx) => {
                        const player = teamAPlayers[idx];
                        return (
                          <div
                            key={idx}
                            className="flex justify-between border-b border-border pb-1 text-sm min-h-[1.5rem]"
                          >
                            <span className="text-foreground">{player?.full_name || ''}</span>
                            <span className="font-mono text-muted-foreground">
                              {player ? Number(player.points_scored).toFixed(1) : ''}
                            </span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Team B */}
                    <div className="space-y-1 text-right">
                      {Array.from({ length: maxPlayers }).map((_, idx) => {
                        const player = teamBPlayers[idx];
                        return (
                          <div
                            key={idx}
                            className="flex justify-between border-b border-border pb-1 text-sm min-h-[1.5rem]"
                          >
                            <span className="font-mono text-muted-foreground">
                              {player ? Number(player.points_scored).toFixed(1) : ''}
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
