import type { GetMatchups } from '@/features/standings/types';

interface ScoreboardCardProps {
  matchup: GetMatchups['data'][number];
  onClick?: () => void;
}

export function ScoreboardCard({ matchup, onClick }: ScoreboardCardProps) {
  const isTeamAWinner = matchup.winner === matchup.team_a_member_id;
  const isTeamBWinner = matchup.winner === matchup.team_b_member_id;

  return (
    <div onClick={onClick} className="bg-card shadow rounded-md p-4 w-full max-w-md mx-auto cursor-pointer">
      {/* Team A */}
      <div className="flex justify-between items-center py-2 border-b border-border">
        <div className="text-left">
          <div className={`text-lg ${isTeamAWinner ? 'font-bold' : ''}`}>{matchup.team_a_team_name}</div>
          <div className={`text-sm text-muted-foreground ${isTeamAWinner ? 'font-bold text-foreground' : ''}`}>
            {matchup.team_a_full_name}
          </div>
        </div>
        <div className={`text-right text-lg ${isTeamAWinner ? 'font-bold' : ''}`}>
          {parseFloat(matchup.team_a_score).toFixed(2)}
        </div>
      </div>

      {/* Team B */}
      <div className="flex justify-between items-center py-2">
        <div className="text-left">
          <div className={`text-lg ${isTeamBWinner ? 'font-bold' : ''}`}>{matchup.team_b_team_name}</div>
          <div className={`text-sm text-muted-foreground ${isTeamBWinner ? 'font-bold text-foreground' : ''}`}>
            {matchup.team_b_full_name}
          </div>
        </div>
        <div className={`text-right text-lg ${isTeamBWinner ? 'font-bold' : ''}`}>
          {parseFloat(matchup.team_b_score).toFixed(2)}
        </div>
      </div>
    </div>
  );
}
