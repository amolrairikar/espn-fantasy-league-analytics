import { Skeleton } from '@/components/ui/skeleton';

export function TableSkeleton() {
  return (
    <div className="space-y-2">
      {/* Example skeletons mimicking a small table or list */}
      <Skeleton className="h-6 w-3/4 mx-auto" />
      <Skeleton className="h-6 w-3/4 mx-auto" />
      <Skeleton className="h-6 w-3/4 mx-auto" />
      <Skeleton className="h-6 w-3/4 mx-auto" />
    </div>
  );
}
