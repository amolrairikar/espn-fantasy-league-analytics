import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import type { GetMatchups } from '@/features/standings/types';

interface MatchupSheetProps {
  matchup: GetMatchups['data'][number];
  open: boolean;
  onClose: () => void;
}

export function MatchupSheet({ matchup, open, onClose }: MatchupSheetProps) {
  return (
    <Sheet open={open} onOpenChange={(val) => !val && onClose()}>
      <SheetContent className="w-full max-w-lg md:max-w-3xl">
        <SheetHeader>
          <SheetTitle>Matchup Details</SheetTitle>
        </SheetHeader>
        <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(matchup, null, 2)}</pre>
      </SheetContent>
    </Sheet>
  );
}
