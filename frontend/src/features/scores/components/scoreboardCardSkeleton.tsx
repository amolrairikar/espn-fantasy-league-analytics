export function ScoreboardCardSkeleton() {
  return (
    <div className="relative w-full max-w-md mx-auto animate-pulse">
      {/* Skeleton Card Container */}
      <div className="bg-card border border-border shadow rounded-md p-4 w-full">
        
        {/* Team A Row */}
        <div className="flex justify-between items-center py-2 border-b border-border">
          <div className="space-y-2">
            {/* Team Name Placeholder */}
            <div className="h-6 w-32 bg-muted rounded" />
            {/* Owner Name & Record Placeholder */}
            <div className="h-4 w-24 bg-muted/60 rounded" />
          </div>
          {/* Score Placeholder */}
          <div className="h-6 w-12 bg-muted rounded" />
        </div>

        {/* Team B Row */}
        <div className="flex justify-between items-center py-2">
          <div className="space-y-2">
            {/* Team Name Placeholder */}
            <div className="h-6 w-36 bg-muted rounded" />
            {/* Owner Name & Record Placeholder */}
            <div className="h-4 w-20 bg-muted/60 rounded" />
          </div>
          {/* Score Placeholder */}
          <div className="h-6 w-12 bg-muted rounded" />
        </div>
      </div>
    </div>
  );
};
