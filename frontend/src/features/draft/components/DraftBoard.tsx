import DraftPickCard from '@/features/draft/components/DraftPickCard';
import type { DraftResultItem } from '@/features/draft/types';
import type { GetDraftResults } from '@/api/draft_results/types';

interface DraftBoardProps {
  draftResults: GetDraftResults['data'];
};

function DraftBoard({ draftResults }: DraftBoardProps) {
  if (!draftResults.length) return null;

  // Normalize numeric fields
  const normalized: DraftResultItem[] = draftResults.map((d) => ({
    ...d,
    pick_number: Number(d.pick_number),
    round: Number(d.round),
    overall_pick_number: Number(d.overall_pick_number),
  }));

  // Get unique owners in draft order (round 1 order)
  const round1Picks = normalized
    .filter((p) => p.round === 1)
    .sort((a, b) => a.overall_pick_number - b.overall_pick_number);

  const owners = round1Picks.map((p) => p.owner_full_name);

  // Initialize empty columns
  const picksByOwner: Record<string, DraftResultItem[]> = {};
  owners.forEach((owner) => {
    picksByOwner[owner] = [];
  });

  // Group picks by round, applying snake order per round
  const maxRound = Math.max(...normalized.map((p) => p.round));
  for (let round = 1; round <= maxRound; round++) {
    const roundPicks = normalized.filter((p) => p.round === round);

    // Snake order: even rounds reverse owner order
    const roundOwners =
      round % 2 === 0 ? [...owners].reverse() : owners;

    roundOwners.forEach((owner) => {
      const pick = roundPicks.find((p) => p.owner_full_name === owner);
      if (pick) {
        picksByOwner[owner].push(pick);
      }
    });
  }

  return (
    <div className="grid grid-flow-col auto-cols-max gap-6 p-4 overflow-x-auto">
      {owners.map((owner) => (
        <div key={owner} className="flex flex-col">
          <h2 className="text-xl font-bold mb-3 text-center">{owner}</h2>
          {picksByOwner[owner].map((pick) => (
            <DraftPickCard key={pick.overall_pick_number} pick={pick} />
          ))}
        </div>
      ))}
    </div>
  );
}

export default DraftBoard;
