import { useCallback, useEffect, useState } from 'react';
import type { GetSeasonStandings, StandingsProps, Team } from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import type { GetLeagueMetadata } from '@/features/login/types';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useSidebar } from '@/components/ui/sidebar';
import { AgGridReact } from 'ag-grid-react';
import {
  ModuleRegistry,
  AllCommunityModule,
  type GridReadyEvent,
  type ValueGetterParams,
  type ValueFormatterParams,
} from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

// eslint-disable-next-line @typescript-eslint/no-unsafe-call,@typescript-eslint/no-unsafe-member-access,@typescript-eslint/no-explicit-any
(ModuleRegistry as any).registerModules([AllCommunityModule]);

function SeasonStandings({ gridApiRef }: StandingsProps) {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const { open: sidebarOpen } = useSidebar();

  const [seasons, setSeasons] = useState<string[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<string | undefined>(undefined);
  const [standingsData, setStandingsData] = useState<Team[]>([]);

  const { refetch: refetchLeagueMetadata } = useGetResource<GetLeagueMetadata>(`/leagues/${leagueData.leagueId}`, {
    platform: leagueData.platform,
  });

  const { refetch: refetchSeasonStandings } = useGetResource<GetSeasonStandings>(`/standings`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    season: selectedSeason,
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchLeagueMetadata();
        const fetchedSeasons = response.data?.data.seasons ?? [];
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
  }, [refetchLeagueMetadata, seasons]);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchSeasonStandings();
        if (response?.data?.data) {
          console.log(response.data.data);
          const transformedData: Team[] = response.data.data.map((team) => {
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

  const onGridReady = useCallback(
    (params: GridReadyEvent) => {
      const autoSizePinnedColumns = () => {
        if (!gridApiRef.current) return;

        const allColumns = gridApiRef.current.getColumns() ?? [];
        const pinnedColumns = allColumns.filter((col) => col.getPinned() === 'left');
        const columnIds = pinnedColumns.map((col) => col.getId());

        if (columnIds.length) {
          gridApiRef.current.autoSizeColumns(columnIds, false);
        }
      };

      gridApiRef.current = params.api;
      autoSizePinnedColumns();
    },
    [gridApiRef],
  );

  // Whenever sidebar is toggled, resize the grid
  useEffect(() => {
    if (!gridApiRef.current) return;

    const timeout = setTimeout(() => {
      const allColumns = gridApiRef.current!.getColumns() ?? [];
      const pinnedColumns = allColumns.filter((col) => col.getPinned() !== 'left');
      const columnIds = pinnedColumns.map((col) => col.getId());

      if (columnIds.length) {
        gridApiRef?.current?.autoSizeColumns(columnIds, false);
      }
    }, 350); // matches sidebar transition duration

    return () => clearTimeout(timeout);
  }, [sidebarOpen, gridApiRef]);

  const DESC = 'desc' as const;
  const LEFT = 'left' as const;

  const columns = [
    { field: 'owner_full_name' as keyof Team, headerName: 'Owner', sortable: true, pinned: LEFT, minWidth: 180 },
    { field: 'record' as keyof Team, headerName: 'Record', flex: 1, minWidth: 80 },
    {
      field: 'win_pct' as keyof Team,
      headerName: 'Win %',
      sortable: true,
      sort: DESC,
      valueFormatter: (params: { value: number }) => (params.value != null ? params.value.toFixed(3) : ''),
      flex: 1,
      minWidth: 90,
    },
    {
      field: 'points_for_per_game' as keyof Team,
      headerName: 'PF / Game',
      sortable: true,
      valueGetter: (params: ValueGetterParams<Team, number>) => {
        const value = params.data?.points_for_per_game;
        return value ?? null; // return number, not string
      },
      valueFormatter: (params: ValueFormatterParams<Team, number>) =>
        params.value != null ? params.value.toFixed(1) : '',
      flex: 1,
      minWidth: 95,
    },
    {
      field: 'points_against_per_game' as keyof Team,
      headerName: 'PA / Game',
      sortable: true,
      valueGetter: (params: ValueGetterParams<Team, number>) => {
        const value = params.data?.points_against_per_game;
        return value ?? null;
      },
      valueFormatter: (params: ValueFormatterParams<Team, number>) =>
        params.value != null ? params.value.toFixed(1) : '',
      flex: 1,
      minWidth: 95,
    },
  ];

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

      {selectedSeason && standingsData ? (
        <div className="ag-theme-alpine my-2" style={{ overflowX: 'auto', maxWidth: '620px', width: '100%' }}>
          <AgGridReact
            rowData={standingsData}
            columnDefs={columns}
            defaultColDef={{ resizable: true }}
            domLayout="autoHeight"
            onGridReady={onGridReady}
          />
        </div>
      ) : (
        <p className="text-sm text-muted-foreground italic"> Please select a season to view standings. </p>
      )}
    </div>
  );
}

export default SeasonStandings;
