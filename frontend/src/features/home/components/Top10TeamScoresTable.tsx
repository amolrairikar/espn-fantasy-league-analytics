import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export interface TeamScoreRow {
  owner_full_name: string;
  points_scored: string | number;
  season: number;
  week: number;
  owner_id: string;
}

export type Top10TeamScoreProps = {
  data: TeamScoreRow[] | null;
};

export function Top10TeamScores({ data }: Top10TeamScoreProps) {
  // Guard clause for null or empty data
  if (!data || data.length === 0) {
    return <div className="p-4 text-center text-muted-foreground">No scoring data found.</div>;
  }

  return (
    <div className="w-full">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="text-center">Name</TableHead>
            <TableHead className="text-center">Score</TableHead>
            <TableHead className="text-center">Season</TableHead>
            <TableHead className="text-center">Week</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((team, idx) => (
            <TableRow key={`${team.owner_id}-${idx}`}>
              <TableCell className="text-center">{team.owner_full_name}</TableCell>
              <TableCell className="text-center">
                {/* Defensive rendering: ensuring points_scored is a string for parseFloat */}
                {parseFloat(team.points_scored?.toString() ?? '0').toFixed(2)}
              </TableCell>
              <TableCell className="text-center">{team.season}</TableCell>
              <TableCell className="text-center">{team.week}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
