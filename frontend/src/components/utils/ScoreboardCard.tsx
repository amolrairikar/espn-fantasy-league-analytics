import type { GetMatchups } from '@/features/standings/types';

interface ScoreboardCardProps {
  matchup: GetMatchups['data'][number];
  onClick?: () => void;
}

export function ScoreboardCard({ matchup, onClick }: ScoreboardCardProps) {
  const isTeamAWinner = matchup.winner === matchup.team_a_member_id;
  const isTeamBWinner = matchup.winner === matchup.team_b_member_id;

  return (
    <div onClick={onClick} className="bg-white shadow rounded-md p-4 w-full max-w-md mx-auto cursor-pointer">
      {/* Team A */}
      <div className="flex justify-between items-center py-2 border-b border-gray-200">
        <div className="text-left">
          <div className={`text-lg ${isTeamAWinner ? 'font-bold' : ''}`}>{matchup.team_a}</div>
          <div className={`text-sm text-gray-500 ${isTeamAWinner ? 'font-bold text-black' : ''}`}>
            {matchup.team_a_member_id}
          </div>
        </div>
        <div className={`text-right text-lg ${isTeamAWinner ? 'font-bold' : ''}`}>
          {parseFloat(matchup.team_a_score).toFixed(1)}
        </div>
      </div>

      {/* Team B */}
      <div className="flex justify-between items-center py-2">
        <div className="text-left">
          <div className={`text-lg ${isTeamBWinner ? 'font-bold' : ''}`}>{matchup.team_b}</div>
          <div className={`text-sm text-gray-500 ${isTeamBWinner ? 'font-bold text-black' : ''}`}>
            {matchup.team_b_member_id}
          </div>
        </div>
        <div className={`text-right text-lg ${isTeamBWinner ? 'font-bold' : ''}`}>
          {parseFloat(matchup.team_b_score).toFixed(1)}
        </div>
      </div>
    </div>
  );
}
