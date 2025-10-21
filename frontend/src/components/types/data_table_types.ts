import { type Column } from '@tanstack/react-table';

type SortableHeaderProps<T> = {
  column: Column<T>;
  label: string;
};

export type { SortableHeaderProps };
