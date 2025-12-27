import { useState } from 'react';
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from '@tanstack/react-table';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  initialSorting?: SortingState;
  onRowClick?: (row: TData) => void;
  selectedRow?: TData | null;
}

export function DataTable<TData, TValue>({
  columns,
  data,
  initialSorting = [],
  onRowClick,
  selectedRow,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>(initialSorting);
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    state: {
      sorting,
    },
  });

  return (
    <div className="overflow-x-auto rounded-md border">
      <Table>
        <TableHeader className="bg-background">
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header, headerIndex) => {
                return (
                  <TableHead
                    key={header.id}
                    className={
                      headerIndex === 0
                        ? 'sticky left-0 bg-background z-20 shadow-[2px_0_4px_rgba(0,0,0,0.05)]'
                        : 'z-10 bg-background'
                    }
                  >
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                );
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => {
              const isSelected = selectedRow
                ? row.original === selectedRow
                : false;

              return (
                <TableRow
                  key={row.id}
                  className={`cursor-pointer transition 
                    ${isSelected ? 'bg-muted outline-2 outline-ring' : 'hover:bg-muted'}
                  `}
                  onClick={() => onRowClick?.(row.original)}
                >
                  {row.getVisibleCells().map((cell, cellIndex) => (
                    <TableCell
                      key={cell.id}
                      className={`${
                        cellIndex === 0
                          ? 'sticky left-0 z-10 shadow-[2px_0_4px_rgba(0,0,0,0.05)] bg-background'
                          : ''
                      }`}
                    >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                  ))}
                </TableRow>
              );
            })
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                No results.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
