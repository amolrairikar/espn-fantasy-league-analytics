import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { GetChampionshipWinners } from '@/features/home/types';

type ChampionshipWinnersProps = {
  data: GetChampionshipWinners['data'];
};

export function ChampionshipWinners({ data }: ChampionshipWinnersProps) {
  const sortedData = [...data].sort((a, b) => {
    const diff = Number(b.championships_won) - Number(a.championships_won);
    if (diff !== 0) return diff; // sort by championships first
    return a.owner_full_name.localeCompare(b.owner_full_name); // then sort by name
  });

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Championships</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedData.map((winner) => (
          <TableRow key={winner.owner_member_id}>
            <TableCell>{winner.owner_full_name}</TableCell>
            <TableCell>{winner.championships_won}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
