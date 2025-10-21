import { ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { SortableHeaderProps } from '@/components/types/data_table_types';

export function SortableHeader<T>({ column, label }: SortableHeaderProps<T>) {
  const sort = column.getIsSorted();

  return (
    <div className="relative w-full flex items-center justify-center">
      <p className="m-0 text-center w-full">{label}</p>
      <Button
        variant="ghost"
        className="cursor-pointer absolute right-0 p-0 w-auto flex items-center gap-1"
        onClick={() => column.toggleSorting(sort === 'asc')}
      >
        {sort === 'asc' ? (
          <ArrowUp className="h-4 w-4" />
        ) : sort === 'desc' ? (
          <ArrowDown className="h-4 w-4" />
        ) : (
          <ArrowUpDown className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
}
