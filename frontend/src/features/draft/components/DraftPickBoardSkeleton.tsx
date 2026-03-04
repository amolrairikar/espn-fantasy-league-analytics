import { Skeleton } from "@/components/ui/skeleton";

export function DraftPickSkeleton() {
  return (
    <div className="mb-3 rounded-2xl h-35 w-50 flex flex-col justify-center px-4 py-4 bg-muted/50 border border-muted">
      {/* Mimic Player Name */}
      <div className="flex justify-center mb-4">
        <Skeleton className="h-6 w-3/4" />
      </div>

      <div className="flex flex-row justify-between items-center px-1 w-full mt-auto">
        {/* Mimic Left Side (Pos/Pick) */}
        <div className="flex flex-col space-y-2">
          <Skeleton className="h-3 w-8" />
          <Skeleton className="h-3 w-12" />
        </div>
        
        {/* Mimic Delta Pill */}
        <Skeleton className="h-6 w-10 rounded-full" />
      </div>
    </div>
  );
}

export function DraftBoardSkeleton() {
  // Mocking a standard 10-team, 16-round layout
  const columns = Array.from({ length: 10 });
  const rows = Array.from({ length: 16 });

  return (
    <div className="grid grid-flow-col auto-cols-max gap-6 p-4 overflow-x-auto animate-pulse">
      {columns.map((_, colIdx) => (
        <div key={colIdx} className="flex flex-col">
          {/* Mimic Owner Header */}
          <div className="flex justify-center mb-3">
            <Skeleton className="h-7 w-32" />
          </div>
          
          {/* Mimic Column of Picks */}
          {rows.map((_, rowIdx) => (
            <DraftPickSkeleton key={rowIdx} />
          ))}
        </div>
      ))}
    </div>
  );
}