import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export interface ChampionshipRow {
  owner_full_name: string;
  championships_won: number;
}

export type ChampionshipWinnersProps = {
  data: ChampionshipRow[] | null;
};

export function ChampionshipWinners({ data }: ChampionshipWinnersProps) {
  if (!data || data.length === 0) {
    return <div className="p-4 text-center text-muted-foreground">No championship data found.</div>;
  }

  return (
    <div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-50 text-center">Owner</TableHead>
            <TableHead className="text-center">Championships</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((winner) => (
            <TableRow key={winner.owner_full_name}>
              <TableCell className="text-center">
                {winner.owner_full_name}
              </TableCell>
              <TableCell className="text-center">
                {/* 2. Defensive rendering: Convert to String to avoid BigInt render errors */}
                {winner.championships_won.toString()}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
