import { recordConfigs } from '@/features/home/utils/recordConfigs';
import { TableSkeleton } from '@/features/home/utils/TableSkeleton';
import type { ChampionshipRow } from '@/features/home/components/ChampionshipWinnersTable'
import type { TeamScoreRow } from '@/features/home/components/Top10TeamScoresTable';
import type { PlayerScoreRow } from '@/features/home/components/Top10PlayerScoresTable';

interface AllTimeRecordsProps {
  champions: ChampionshipRow[] | null;
  topScores: TeamScoreRow[] | null;
  bottomScores: TeamScoreRow[] | null;
  qbScores: PlayerScoreRow[] | null;
  rbScores: PlayerScoreRow[] | null;
  wrScores: PlayerScoreRow[] | null;
  teScores: PlayerScoreRow[] | null;
  dstScores: PlayerScoreRow[] | null;
  kScores: PlayerScoreRow[] | null;
}

function AllTimeRecords({ 
  champions, topScores, bottomScores, qbScores, rbScores, wrScores, teScores, dstScores, kScores
}: AllTimeRecordsProps) {

  const dataMap: Record<string, any[] | null> = {
    champions: champions,
    topTeams: topScores,
    bottomTeams: bottomScores,
    qb: qbScores,
    rb: rbScores,
    wr: wrScores,
    te: teScores,
    dst: dstScores,
    k: kScores,
  };

  return (
    <div className="w-full px-4 sm:px-4">
      <h1 className="text-3xl font-bold text-center">🏆 Hall of Fame 🏆</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
        {recordConfigs.map(({ key, label, component: Component }) => {
          const data = dataMap[key as keyof typeof dataMap];
          return (
            <div key={key}>
              <h2 className="text-lg font-semibold mb-4 text-center">{label}</h2>
              {!data ? (
                <TableSkeleton />
              ) : (
                // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-assignment
                <Component data={data as any} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default AllTimeRecords;
