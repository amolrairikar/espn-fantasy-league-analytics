import { useCallback, useEffect, useRef, useState } from 'react';
import type { GetAllTimeStandings, Team } from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { Separator } from '@/components/ui/separator';
import { useSidebar } from '@/components/ui/sidebar';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule, type GridApi, type GridReadyEvent } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

// eslint-disable-next-line @typescript-eslint/no-unsafe-call,@typescript-eslint/no-unsafe-member-access,@typescript-eslint/no-explicit-any
(ModuleRegistry as any).registerModules([AllCommunityModule]);

function AllTimeStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const gridApiRef = useRef<GridApi | null>(null);
  const { open: sidebarOpen } = useSidebar();

  const [standingsData, setStandingsData] = useState<Team[]>([]);

  const { refetch: refetchAllTimeStandings } = useGetResource<GetAllTimeStandings>(`/standings`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchAllTimeStandings();
        if (response?.data?.data) {
          console.log(response.data.data);
          const transformedData: Team[] = response.data.data.map((team) => ({
            ...team,
            games_played: Number(team.games_played),
            wins: Number(team.wins),
            losses: Number(team.losses),
            win_pct: parseFloat(team.win_pct),
            points_for_per_game: parseFloat(team.points_for_per_game),
            points_against_per_game: parseFloat(team.points_against_per_game),
          }));
          setStandingsData(transformedData);
        }
      } catch (err) {
        console.error(err);
      }
    };

    void fetchStatus();
  }, [refetchAllTimeStandings]);

  const onGridReady = useCallback((params: GridReadyEvent) => {
    gridApiRef.current = params.api;
    params.api.sizeColumnsToFit();
  }, []);

  // Whenever sidebar is toggled, resize the grid
  useEffect(() => {
    if (!gridApiRef.current) return;

    const timeout = setTimeout(() => {
      gridApiRef.current?.sizeColumnsToFit();
    }, 350); // matches sidebar transition duration

    return () => clearTimeout(timeout);
  }, [sidebarOpen]);

  const DESC = 'desc' as const;

  const columns = [
    { field: 'owner_full_name' as keyof Team, headerName: 'Owner', sortable: true },
    { field: 'games_played' as keyof Team, headerName: 'GP', sortable: true },
    { field: 'wins' as keyof Team, headerName: 'Wins', sortable: true, sort: DESC },
    { field: 'losses' as keyof Team, headerName: 'Losses', sortable: true },
    {
      field: 'win_pct' as keyof Team,
      headerName: 'Win %',
      sortable: true,
      valueFormatter: (params: { value: number }) => (params.value != null ? params.value.toFixed(3) : ''),
    },
    {
      field: 'points_for_per_game' as keyof Team,
      headerName: 'Points / Game',
      sortable: true,
      valueFormatter: (params: { value: number }) => (params.value != null ? params.value.toFixed(1) : ''),
    },
    {
      field: 'points_against_per_game' as keyof Team,
      headerName: 'Points Against / Game',
      sortable: true,
      valueFormatter: (params: { value: number }) => (params.value != null ? params.value.toFixed(1) : ''),
    },
  ];

  return (
    <div>
      <div className="ag-theme-alpine" style={{ width: '100%' }}>
        <AgGridReact
          rowData={standingsData}
          columnDefs={columns}
          defaultColDef={{ resizable: true }}
          domLayout="autoHeight"
          onGridReady={onGridReady}
        />
      </div>
      <Separator className="my-4" />
      <p className="my-2">Testing!</p>
    </div>
  );
}

export default AllTimeStandings;
