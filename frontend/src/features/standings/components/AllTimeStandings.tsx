import { useCallback, useEffect, useState } from 'react';
import type { GetAllTimeStandings, StandingsProps, Team } from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
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

function AllTimeStandings({ gridApiRef }: StandingsProps) {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const { open: sidebarOpen } = useSidebar();

  // const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);
  const [standingsData, setStandingsData] = useState<Team[]>([]);

  const { refetch: refetchAllTimeStandings } = useGetResource<GetAllTimeStandings['data']>(`/standings`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchAllTimeStandings();
        if (response?.data?.data) {
          console.log(response.data.data);
          const transformedData: Team[] = response.data.data.map((team) => {
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

  // Auto-size only pinned column (Owner)
  const onGridReady = useCallback(
    (params: GridReadyEvent) => {
      if (!gridApiRef.current) return;
      gridApiRef.current = params.api;
      const allColumns = gridApiRef.current.getColumns() ?? [];
      const pinnedColumns = allColumns.filter((col) => col.getPinned() === 'left');
      const columnIds = pinnedColumns.map((col) => col.getId());
      if (columnIds.length) {
        gridApiRef.current.autoSizeColumns(columnIds, false);
      }
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
    { field: 'games_played' as keyof Team, headerName: 'GP', sortable: true, flex: 1, minWidth: 80 },
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
    <div>
      {/* <p className="italic">Click on an owner's name to display additional charts!</p> */}
      <div className="ag-theme-alpine my-2" style={{ overflowX: 'auto', maxWidth: '689px', width: '100%' }}>
        <AgGridReact
          rowData={standingsData}
          columnDefs={columns}
          defaultColDef={{ resizable: true }}
          domLayout="autoHeight"
          onGridReady={onGridReady}
        />
      </div>
    </div>
  );
}

export default AllTimeStandings;
