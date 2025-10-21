import { useEffect, useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import type {
  GetAllTimeStandings,
  GetAllTimeStandingsBySeason,
  GetLeagueMembers,
  Member,
  MemberConfig,
  StandingsAllTime,
  StandingsAllTimeBySeason,
} from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { DataTable } from '@/components/utils/dataTable';
import { SortableHeader } from '@/components/utils/sortableColumnHeader';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';

function AllTimeStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const [standingsData, setStandingsData] = useState<StandingsAllTime[]>([]);
  const [standingsDataAllSeasons, setStandingsDataAllSeasons] = useState<StandingsAllTimeBySeason[]>([]);
  const [members, setMembers] = useState<MemberConfig[]>([]);
  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);
  const selectedOwnerId = members.find((m) => m.name === selectedOwnerName)?.member_id ?? undefined;

  const columns: ColumnDef<StandingsAllTime>[] = [
    {
      accessorKey: 'owner_full_name',
      header: 'Owner',
      cell: ({ row }) => {
        const isSelected = row.original.owner_full_name === selectedOwnerName;
        return (
          <div
            className={`cursor-pointer hover:bg-muted px-2 py-1 rounded transition 
                        ${isSelected ? 'outline-2 outline-ring' : ''}`}
            onClick={() => setSelectedOwnerName(row.original.owner_full_name)}
          >
            {row.original.owner_full_name}
          </div>
        );
      },
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

  const { refetch: refetchAllTimeStandings } = useGetResource<GetAllTimeStandings['data']>(`/standings`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    standings_type: 'all_time',
  });

  const { refetch: refetchLeaguemembers } = useGetResource<GetLeagueMembers['data']>(`/members`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
  });

  const { refetch: refetchAllSeasonStandings } = useGetResource<GetAllTimeStandingsBySeason['data']>(`/standings`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    standings_type: 'season',
    team: selectedOwnerId,
  });

  const chartConfig = {
    desktop: {
      label: 'Wins',
      color: 'var(--chart-1)',
    },
  } satisfies ChartConfig;

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchAllTimeStandings();
        if (response?.data?.data) {
          console.log(response.data.data);
          const transformedData: StandingsAllTime[] = response.data.data.map((team) => {
            const wins = Number(team.wins);
            const losses = Number(team.losses);
            return {
              ...team,
              games_played: Number(team.games_played),
              record: `${wins}-${losses}`,
              win_pct: parseFloat(team.win_pct),
              points_for_per_game: parseFloat(team.points_for_per_game),
              points_against_per_game: parseFloat(team.points_against_per_game),
            };
          });
          setStandingsData(transformedData);
        }
      } catch (err) {
        console.error(err);
      }
    };

    void fetchStatus();
  }, [refetchAllTimeStandings]);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchLeaguemembers();
        if (response.data?.data) {
          const membersData = response.data?.data as Member[];
          const mappedMembers = membersData.map((item) => ({
            name: item.name,
            member_id: item.member_id,
          }));
          console.log(mappedMembers);
          setMembers(mappedMembers);
        }
      } catch (err) {
        console.error(err);
      }
    };
    void fetchStatus();
  }, [refetchLeaguemembers]);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        if (!selectedOwnerId) return;
        const response = await refetchAllSeasonStandings();
        if (response?.data?.data) {
          console.log(response.data.data);
          const transformedData: StandingsAllTimeBySeason[] = response.data.data.map(({ season, wins }) => ({
            season,
            wins,
          }));
          setStandingsDataAllSeasons(transformedData);
        }
      } catch (err) {
        console.error(err);
      }
    };

    void fetchStatus();
  }, [refetchAllSeasonStandings, selectedOwnerId]);

  return (
    <div className="space-y-4 my-4">
      <h1 className="font-semibold">All-Time Standings</h1>
      <DataTable columns={columns} data={standingsData} initialSorting={[{ id: 'win_pct', desc: true }]} />
      {selectedOwnerName ? (
        <div className="space-y-2">
          <h1 className="font-semibold text-center">Wins Per Season for {selectedOwnerName}</h1>
          <ChartContainer config={chartConfig} className="h-[200px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart accessibilityLayer data={standingsDataAllSeasons}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="season" tickLine={false} tickMargin={10} axisLine={false} />
                <YAxis dataKey="wins" />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="wins" fill="var(--color-desktop)" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>
      ) : (
        <p className="italic">Click on an owner's name to display a chart of their wins per season</p>
      )}
    </div>
  );
}

export default AllTimeStandings;
