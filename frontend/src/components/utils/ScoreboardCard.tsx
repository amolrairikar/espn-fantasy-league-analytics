import type { Matchup } from '@/features/scores/types';

interface TeamWeeklyRecord {
  owner_id: string;
  wins: number;
  losses: number;
  ties: number;
}

interface ScoreboardCardProps {
  matchup: Matchup;
  team_records: TeamWeeklyRecord[];
  onClick?: () => void;
}

export function ScoreboardCard({ matchup, team_records, onClick }: ScoreboardCardProps) {
  const isTeamAWinner = matchup.winner === matchup.home_team_id;
  const isTeamBWinner = matchup.winner === matchup.away_team_id;
  const isPlayoff = matchup.playoff_tier_type === 'WINNERS_BRACKET';
  const teamARecord = team_records.find(
    (record) => record.owner_id === matchup.home_team_owner_id
  );
  const teamBRecord = team_records.find(
    (record) => record.owner_id === matchup.away_team_owner_id
  );
  const formatRecord = (rec?: TeamWeeklyRecord) => 
    rec ? `${rec.wins}-${rec.losses}-${rec.ties}` : "0-0-0";

  console.log({
    winner: matchup.winner,
    winnerType: typeof matchup.winner,
    homeId: matchup.home_team_id,
    homeIdType: typeof matchup.home_team_id,
    match: matchup.winner === matchup.home_team_id
  });

  return (
    <div className="relative w-full max-w-md mx-auto cursor-pointer" onClick={onClick}>
      {/* PLAYOFF badge */}
      {isPlayoff && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-md shadow-sm border border-border">
          PLAYOFF
        </div>
      )}

      {/* Scoreboard card */}
      <div className="bg-card shadow rounded-md p-4 w-full">
        {/* Team A (Home team) */}
        <div className="flex justify-between items-center py-2 border-b border-border">
          <div className="text-left">
            <div className={`text-lg ${isTeamAWinner ? 'font-bold' : ''}`}> {matchup.home_team_team_name} </div>
            <div className={`text-sm text-muted-foreground ${isTeamAWinner ? 'font-bold text-foreground' : ''}`}>
              {matchup.home_team_full_name}{' '}
              {matchup.playoff_tier_type === 'NONE' && (
                <span className="text-xs text-muted-foreground">({formatRecord(teamARecord)})</span>
              )}
            </div>
          </div>
          <div className={`text-right text-lg ${isTeamAWinner ? 'font-bold' : ''}`}>
            {Number(matchup.home_team_score).toFixed(2)}
          </div>
        </div>

        {/* Team B (Away team) */}
        <div className="flex justify-between items-center py-2">
          <div className="text-left">
            <div className={`text-lg ${isTeamBWinner ? 'font-bold' : ''}`}> {matchup.away_team_team_name} </div>
            <div className={`text-sm text-muted-foreground ${isTeamBWinner ? 'font-bold text-foreground' : ''}`}>
              {matchup.away_team_full_name}{' '}
              {matchup.playoff_tier_type === 'NONE' && (
                <span className="text-xs text-muted-foreground">({formatRecord(teamBRecord)})</span>
              )}
            </div>
          </div>
          <div className={`text-right text-lg ${isTeamBWinner ? 'font-bold' : ''}`}>
            {Number(matchup.away_team_score).toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}
