import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { type ColumnDef } from '@tanstack/react-table';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import type { StandingsAllTime } from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { DataTable } from '@/components/utils/dataTable';
import { SortableHeader } from '@/components/utils/sortableColumnHeader';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { fetchAllTimeStandings, fetchMultipleSeasonStandings } from '@/api/standings/api_calls';
import { useFetchLeagueOwners } from '@/components/hooks/fetchOwners';
import { StandingsTableSkeleton } from '@/features/standings/components/SkeletonStandingsTable';
import { GraphSkeleton } from '@/features/standings/components/GraphSkeleton';

function useFetchAllTimeStandings(
  league_id: string,
  platform: string,
  standings_type: string,
) {
  return useQuery({
    queryKey: ['all_time_standings', league_id, platform, standings_type],
    queryFn: () => fetchAllTimeStandings(
      league_id,
      platform,
      standings_type,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!standings_type, // only run if input args are available
  });
};

function useFetchMultipleSeasonStandings(
  league_id: string,
  platform: string,
  standings_type: string,
  team: string,
) {
  return useQuery({
    queryKey: ['multiple_season_standings', league_id, platform, standings_type, team],
    queryFn: () => fetchMultipleSeasonStandings(
      league_id,
      platform,
      standings_type,
      team,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!standings_type && !!team, // only run if input args are available
  });
};

function AllTimeStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);

  const { data: rawStandings, isLoading: loadingStandings } = useFetchAllTimeStandings(
    leagueData!.leagueId,
    leagueData!.platform,
    'all_time'
  );

  const { data: ownersData } = useFetchLeagueOwners(
    leagueData!.leagueId,
    leagueData!.platform
  );

  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);

  const members = ownersData?.data ?? [];
  const selectedOwnerId = members.find((m) => m.owner_full_name === selectedOwnerName)?.owner_id ?? undefined;

  const { data: rawSeasonData, isLoading: loadingSeasonStandingsData } = useFetchMultipleSeasonStandings(
    leagueData!.leagueId,
    leagueData!.platform,
    'season',
    selectedOwnerId!,
  )

  const standingsData = useMemo(() => {
    if (!rawStandings?.data) return [];
    return rawStandings.data.map((team: any) => ({
      ...team,
      games_played: Number(team.games_played),
      record: `${Number(team.wins)}-${Number(team.losses)}-${Number(team.ties)}`,
      win_pct: parseFloat(team.win_pct),
      points_for_per_game: parseFloat(team.points_for_per_game),
      points_against_per_game: parseFloat(team.points_against_per_game),
    }));
  }, [rawStandings]);

  const standingsDataAllSeasons = useMemo(() => {
    if (!rawSeasonData?.data) return [];
    return rawSeasonData.data.map(({ season, wins }: { season: string, wins: string }) => ({ 
      season, 
      wins 
    }));
  }, [rawSeasonData]);

  const columns: ColumnDef<StandingsAllTime>[] = [
    {
      accessorKey: 'owner_full_name',
      header: 'Owner',
      cell: ({ row }) => <div className="px-2 py-1">{row.original.owner_full_name}</div>,
    },
    {
      accessorKey: 'games_played',
      header: () => <div className="w-full text-center">GP</div>,
      cell: ({ row }) => <div className="text-center">{row.original.games_played}</div>,
    },
    {
      accessorKey: 'record',
      header: () => <div className="w-full text-center">Record</div>,
      cell: ({ row }) => <div className="text-center">{row.original.record}</div>,
    },
    {
      accessorKey: 'win_pct',
      header: ({ column }) => (
        <div className="w-full text-center min-w-[100px]">
          <SortableHeader column={column} label="Win %" />
        </div>
      ),
      cell: ({ row }) => <div className="text-center">{row.original.win_pct.toFixed(3)}</div>,
      minSize: 100,
    },
    {
      accessorKey: 'points_for_per_game',
      header: ({ column }) => (
        <div className="w-full text-center min-w-[130px]">
          <SortableHeader column={column} label="PF / Game" />
        </div>
      ),
      cell: ({ row }) => <div className="text-center">{row.original.points_for_per_game.toFixed(1)}</div>,
      minSize: 130,
    },
    {
      accessorKey: 'points_against_per_game',
      header: ({ column }) => (
        <div className="w-full text-center min-w-[130px]">
          <SortableHeader column={column} label="PA / Game" />
        </div>
      ),
      cell: ({ row }) => <div className="text-center">{row.original.points_against_per_game.toFixed(1)}</div>,
      minSize: 130,
    },
  ];

  const chartConfig = {
    desktop: {
      label: 'Wins',
      color: 'var(--chart-1)',
    },
  } satisfies ChartConfig;

  if (loadingStandings) return <StandingsTableSkeleton/>;

  return (
    <div className="space-y-4 my-4 px-2">
      <h1 className="font-semibold px-2">All-Time Standings</h1>
      {selectedOwnerName ? (
        <div className="space-y-2">
          <DataTable
            columns={columns}
            data={standingsData}
            initialSorting={[{ id: 'win_pct', desc: true }]}
            selectedRow={standingsData.find(team => team.owner_full_name === selectedOwnerName) ?? null}
            onRowClick={(row) => setSelectedOwnerName(row.owner_full_name)}
          />
          {/* If Graph Data is Loading */}
          {loadingSeasonStandingsData ? (
            <GraphSkeleton />
          ) : (
            <>
              <h1 className="font-semibold text-center">Wins Per Season for {selectedOwnerName}</h1>
              <ChartContainer config={chartConfig} className="h-[200px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart accessibilityLayer data={standingsDataAllSeasons}>
                    <CartesianGrid vertical={false} />
                    <XAxis dataKey="season" tickLine={false} tickMargin={10} axisLine={false} />
                    <YAxis dataKey="wins" domain={[0, 12]} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar dataKey="wins" fill="var(--color-desktop)" radius={4} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            </>
          )}
        </div>
      ) : (
        <div className="space-y-4 my-4 px-2">
          <p className="text-sm text-muted-foreground italic">
            Click on an owner's name to display a chart of their wins per season
          </p>
          <DataTable
            columns={columns}
            data={standingsData}
            initialSorting={[{ id: 'win_pct', desc: true }]}
            selectedRow={standingsData.find(team => team.owner_full_name === selectedOwnerName) ?? null}
            onRowClick={(row) => setSelectedOwnerName(row.owner_full_name)}
          />
        </div>
      )}
    </div>
  );
}

export default AllTimeStandings;
