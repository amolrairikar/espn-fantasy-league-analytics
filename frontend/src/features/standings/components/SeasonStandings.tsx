import { useEffect, useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import type { GetSeasonStandings, StandingsSeason } from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import type { GetLeagueMetadata } from '@/features/login/types';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { DataTable } from '@/components/utils/dataTable';
import { SortableHeader } from '@/components/utils/sortableColumnHeader';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

function SeasonStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const [seasons, setSeasons] = useState<string[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<string | undefined>(undefined);
  const [standingsData, setStandingsData] = useState<StandingsSeason[]>([]);
  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);

  const columns: ColumnDef<StandingsSeason>[] = [
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

  const { refetch: refetchLeagueMetadata } = useGetResource<GetLeagueMetadata['data']>(
    `/leagues/${leagueData.leagueId}`,
    {
      platform: leagueData.platform,
    },
  );

  const { refetch: refetchSeasonStandings } = useGetResource<GetSeasonStandings['data']>(`/standings`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    standings_type: 'season',
    season: selectedSeason,
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchLeagueMetadata();
        const fetchedSeasons = response.data?.data?.seasons ?? [];
        if (fetchedSeasons.length > 0) {
          setSeasons(fetchedSeasons);
          const latestSeason = fetchedSeasons.sort((a, b) => Number(b) - Number(a))[0];
          setSelectedSeason(latestSeason);
        }
      } catch (err) {
        console.error(err);
      }
    };
    void fetchStatus();
  }, [refetchLeagueMetadata]);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchSeasonStandings();
        if (response?.data?.data) {
          console.log(response.data.data);
          const transformedData: StandingsSeason[] = response.data.data.map((team) => {
            const wins = Number(team.wins);
            const losses = Number(team.losses);
            return {
              ...team,
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
  }, [refetchSeasonStandings, selectedSeason]);

  return (
    <div className="space-y-4 my-4">
      <div className="flex items-center space-x-4">
        <label htmlFor="season" className="font-medium text-sm">
          Season:
        </label>
        <Select onValueChange={setSelectedSeason} value={selectedSeason}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select a season" />
          </SelectTrigger>
          <SelectContent>
            {seasons.length > 0 ? (
              seasons.map((season) => (
                <SelectItem key={season} value={season}>
                  {season}
                </SelectItem>
              ))
            ) : (
              <SelectItem disabled value="none">
                No seasons found
              </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>
      {selectedOwnerName ? (
        <div className="space-y-4 my-4">
          <DataTable columns={columns} data={standingsData} initialSorting={[{ id: 'win_pct', desc: true }]} />
          <p>Selected Owner: {selectedOwnerName}</p>
        </div>
      ) : (
        <div className="space-y-4 my-4">
          <p className="text-sm text-muted-foreground italic">
            TODO: Click on an owner's name to display their season schedule results!
          </p>
          <DataTable columns={columns} data={standingsData} initialSorting={[{ id: 'win_pct', desc: true }]} />
        </div>
      )}
    </div>
  );
}

export default SeasonStandings;
