import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export interface PlayerScoreRow {
  player_name: string;
  points_scored: string | number;
  season: number;
  week: number;
  owner_id: string;
}

export type Top10PlayerScoreProps = {
  data: PlayerScoreRow[] | null;
};

export function Top10PlayerScores({ data }: Top10PlayerScoreProps) {
  // Guard clause for null or empty data
  if (!data || data.length === 0) {
    return <div className="p-4 text-center text-muted-foreground">No scoring data found.</div>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="text-center">Player</TableHead>
          <TableHead className="text-center">Points</TableHead>
          <TableHead className="text-center">Season</TableHead>
          <TableHead className="text-center">Week</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((player, idx) => (
          <TableRow key={`${player.owner_id}-${player.player_name}-${player.season}-${player.week}-${idx}`}>
            <TableCell className="text-center">{player.player_name}</TableCell>
            <TableCell className="text-center">
              {/* Defensive rendering: ensuring points_scored is a string for parseFloat */}
              {parseFloat(player.points_scored?.toString() ?? '0').toFixed(2)}
            </TableCell>
            <TableCell className="text-center">{player.season}</TableCell>
            <TableCell className="text-center">{player.week}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
