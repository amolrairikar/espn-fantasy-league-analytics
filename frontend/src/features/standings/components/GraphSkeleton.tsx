import { Skeleton } from "@/components/ui/skeleton";

export function GraphSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-6 w-1/3 mx-auto" /> {/* Title Skeleton */}
      <div className="h-[200px] w-full border rounded-xl p-6 flex items-end justify-around gap-2">
        <Skeleton className="h-[40%] w-full max-w-10" />
        <Skeleton className="h-[70%] w-full max-w-10" />
        <Skeleton className="h-[55%] w-full max-w-10" />
        <Skeleton className="h-[85%] w-full max-w-10" />
        <Skeleton className="h-[60%] w-full max-w-10" />
      </div>
    </div>
  );
};
