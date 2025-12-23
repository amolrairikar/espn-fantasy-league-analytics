import { useQuery } from '@tanstack/react-query';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import type { LeagueData } from '@/features/login/types';
import { recordConfigs } from '@/features/home/utils/recordConfigs';
import { TableSkeleton } from '@/features/home/utils/TableSkeleton';
import { getChampionshipWinner, getPlayerRecords, getTeamRecords } from '@/api/records/api_calls';

function useChampionshipWinner(leagueId: string, platform: string, recordType: string) {
  return useQuery({
    queryKey: ['championshipWinner', leagueId, platform, recordType],
    queryFn: () => getChampionshipWinner(leagueId, platform, recordType),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!leagueId && !!platform && !!recordType, // only run if input args are available
  });
};

function useTeamRecords(leagueId: string, platform: string, recordType: string) {
  return useQuery({
    queryKey: ['teamRecords', leagueId, platform, recordType],
    queryFn: () => getTeamRecords(leagueId, platform, recordType),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!leagueId && !!platform && !!recordType, // only run if input args are available
  });
};

function usePlayerRecords(leagueId: string, platform: string, recordType: string) {
  return useQuery({
    queryKey: ['playerRecords', leagueId, platform, recordType],
    queryFn: () => getPlayerRecords(leagueId, platform, recordType),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!leagueId && !!platform && !!recordType, // only run if input args are available
  });
};

function AllTimeRecords() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);

  const champions = useChampionshipWinner(
    leagueData?.leagueId ?? '',
    leagueData?.platform ?? '',
    'all_time_championships',
  );
  const topTeams = useTeamRecords(
    leagueData?.leagueId ?? '',
    leagueData?.platform ?? '',
    'top_10_team_scores',
  );
  const bottomTeams = useTeamRecords(
    leagueData?.leagueId ?? '',
    leagueData?.platform ?? '',
    'bottom_10_team_scores',
  );
  const topQB = usePlayerRecords(
    leagueData?.leagueId ?? '',
    leagueData?.platform ?? '',
    'top_10_qb_scores',
  );
  const topRB = usePlayerRecords(
    leagueData?.leagueId ?? '',
    leagueData?.platform ?? '',
    'top_10_rb_scores',
  );
  const topWR = usePlayerRecords(
    leagueData?.leagueId ?? '',
    leagueData?.platform ?? '',
    'top_10_wr_scores',
  );
  const topTE = usePlayerRecords(
    leagueData?.leagueId ?? '',
    leagueData?.platform ?? '',
    'top_10_te_scores',
  );
  const topDST = usePlayerRecords(
    leagueData?.leagueId ?? '',
    leagueData?.platform ?? '',
    'top_10_dst_scores',
  );
  const topK = usePlayerRecords(
    leagueData?.leagueId ?? '',
    leagueData?.platform ?? '',
    'top_10_k_scores',
  );

  // Early return if saving league data to local storage fails
  if (!leagueData) {
    return (
      <p>
        League credentials not found in local browser storage. Please try logging in again and if the issue persists,
        create a support ticket.
      </p>
    );
  }

  const dataMap = {
    champions: champions.data?.data,
    topTeams: topTeams.data?.data,
    bottomTeams: bottomTeams.data?.data,
    qb: topQB.data?.data,
    rb: topRB.data?.data,
    wr: topWR.data?.data,
    te: topTE.data?.data,
    dst: topDST.data?.data,
    k: topK.data?.data,
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
