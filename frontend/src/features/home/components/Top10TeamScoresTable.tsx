import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { GetTeamScores } from '@/features/home/types';

type Top10TeamScoreProps = {
  data: GetTeamScores['data'];
  sortOrder?: 'asc' | 'desc';
};

export function Top10TeamScores({ data, sortOrder }: Top10TeamScoreProps) {
  const sortedData = [...data].sort((a, b) => {
    const scoreA = parseFloat(a.score);
    const scoreB = parseFloat(b.score);
    return sortOrder === 'asc' ? scoreA - scoreB : scoreB - scoreA;
  });

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Score</TableHead>
          <TableHead>Season</TableHead>
          <TableHead>Week</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedData.map((team, idx) => (
          <TableRow key={`${team.member_id}-${idx}`}>
            <TableCell>{team.owner_full_name}</TableCell>
            <TableCell>{parseFloat(team.score).toFixed(2)}</TableCell>
            <TableCell>{team.season}</TableCell>
            <TableCell>{team.week}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
