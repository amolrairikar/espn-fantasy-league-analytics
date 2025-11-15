import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { GetPlayerScores } from '@/features/home/types';

type Top10PlayerScoreProps = {
  data: GetPlayerScores['data'];
};

export function Top10PlayerScores({ data }: Top10PlayerScoreProps) {
  const sortedData = [...data].sort((a, b) => parseFloat(b.points_scored) - parseFloat(a.points_scored));

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Player</TableHead>
          <TableHead>Points</TableHead>
          <TableHead>Season</TableHead>
          <TableHead>Week</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedData.map((player, idx) => (
          <TableRow key={`${player.owner_id}-${player.player_name}-${player.season}-${player.week}-${idx}`}>
            <TableCell>{player.player_name}</TableCell>
            <TableCell>{parseFloat(player.points_scored).toFixed(2)}</TableCell>
            <TableCell>{player.season}</TableCell>
            <TableCell>{player.week}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
