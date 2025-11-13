import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import type { LeagueData } from '@/features/login/types';
import { recordConfigs } from '@/features/home/utils/recordConfigs';
import { useGetAllTimeRecord } from '@/features/home/utils/useAllTimeRecord';
import { TableSkeleton } from '@/features/home/utils/TableSkeleton';
import type { GetChampionshipWinners, GetPlayerScores, GetTeamScores } from '../types';

function AllTimeRecords() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);

  if (!leagueData?.leagueId || !leagueData?.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const champions = useGetAllTimeRecord<GetChampionshipWinners['data']>(
    leagueData.leagueId,
    leagueData.platform,
    'all_time_championships',
  );
  const topTeams = useGetAllTimeRecord<GetTeamScores['data']>(
    leagueData.leagueId,
    leagueData.platform,
    'top_10_team_scores',
  );
  const bottomTeams = useGetAllTimeRecord<GetTeamScores['data']>(
    leagueData.leagueId,
    leagueData.platform,
    'bottom_10_team_scores',
  );
  const topQB = useGetAllTimeRecord<GetPlayerScores['data']>(
    leagueData.leagueId,
    leagueData.platform,
    'top_10_qb_scores',
  );
  const topRB = useGetAllTimeRecord<GetPlayerScores['data']>(
    leagueData.leagueId,
    leagueData.platform,
    'top_10_rb_scores',
  );
  const topWR = useGetAllTimeRecord<GetPlayerScores['data']>(
    leagueData.leagueId,
    leagueData.platform,
    'top_10_wr_scores',
  );
  const topTE = useGetAllTimeRecord<GetPlayerScores['data']>(
    leagueData.leagueId,
    leagueData.platform,
    'top_10_te_scores',
  );
  const topDST = useGetAllTimeRecord<GetPlayerScores['data']>(
    leagueData.leagueId,
    leagueData.platform,
    'top_10_dst_scores',
  );
  const topK = useGetAllTimeRecord<GetPlayerScores['data']>(
    leagueData.leagueId,
    leagueData.platform,
    'top_10_k_scores',
  );

  const dataMap = {
    champions,
    topTeams,
    bottomTeams,
    qb: topQB,
    rb: topRB,
    wr: topWR,
    te: topTE,
    dst: topDST,
    k: topK,
  };

  return (
    <div className="w-full px-4 sm:px-4">
      <h1 className="text-3xl font-bold text-center">🏆 Hall of Fame 🏆</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
        {recordConfigs.map(({ key, label, component: Component, sortOrder }) => {
          const data = dataMap[key as keyof typeof dataMap];

          return (
            <div key={key}>
              <h2 className="text-lg font-semibold mb-4 text-center">{label}</h2>
              {!data ? (
                <TableSkeleton />
              ) : data.length === 0 ? (
                <p className="text-center text-muted-foreground">No data available.</p>
              ) : (
                // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-assignment
                <Component data={data as any} sortOrder={(sortOrder as 'asc' | 'desc') ?? 'desc'} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default AllTimeRecords;
