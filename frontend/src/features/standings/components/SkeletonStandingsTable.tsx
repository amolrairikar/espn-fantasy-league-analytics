import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function StandingsTableSkeleton() {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-37.5"><Skeleton className="h-4 w-24" /></TableHead>
            <TableHead><Skeleton className="h-4 w-12 mx-auto" /></TableHead>
            <TableHead><Skeleton className="h-4 w-16 mx-auto" /></TableHead>
            <TableHead><Skeleton className="h-4 w-16 mx-auto" /></TableHead>
            <TableHead><Skeleton className="h-4 w-20 mx-auto" /></TableHead>
            <TableHead><Skeleton className="h-4 w-20 mx-auto" /></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: 10 }).map((_, i) => (
            <TableRow key={i}>
              <TableCell><Skeleton className="h-4 w-32" /></TableCell>
              <TableCell><Skeleton className="h-4 w-8 mx-auto" /></TableCell>
              <TableCell><Skeleton className="h-4 w-12 mx-auto" /></TableCell>
              <TableCell><Skeleton className="h-4 w-12 mx-auto" /></TableCell>
              <TableCell><Skeleton className="h-4 w-16 mx-auto" /></TableCell>
              <TableCell><Skeleton className="h-4 w-16 mx-auto" /></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};
