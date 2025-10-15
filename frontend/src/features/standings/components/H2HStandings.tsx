import { useCallback, useEffect, useRef, useState } from 'react';
import type { GetLeagueMembers, GetH2HStandings, Matchup, Member, Team, GetMatchups } from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useSidebar } from '@/components/ui/sidebar';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule, type GridApi, type GridReadyEvent } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

// eslint-disable-next-line @typescript-eslint/no-unsafe-call,@typescript-eslint/no-unsafe-member-access,@typescript-eslint/no-explicit-any
(ModuleRegistry as any).registerModules([AllCommunityModule]);

function H2HStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const gridApiRef = useRef<GridApi | null>(null);
  const { open: sidebarOpen } = useSidebar();

  type memberConfig = { name: string; member_id: string };
  const [members, setMembers] = useState<memberConfig[]>([]);
  const [selectedOwnerId, setSelectedOwnerId] = useState<string | undefined>(undefined);
  const selectedOwnerName = members.find((m) => m.member_id === selectedOwnerId)?.name ?? null;
  const [selectedOpponentName, setSelectedOpponentName] = useState<string | null>(null);
  const selectedOpponentId = members.find((m) => m.name === selectedOpponentName)?.member_id ?? undefined;
  const [standingsData, setStandingsData] = useState<Team[]>([]);
  const [scoresData, setScoresData] = useState<Matchup[]>([]);

  const { refetch: refetchLeaguemembers } = useGetResource<GetLeagueMembers>(`/members`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
  });

  const { refetch: refetchH2HStandings } = useGetResource<GetH2HStandings>(`/standings`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    h2h_standings: 'true',
  });

  const { refetch: refetchH2HMatchups } = useGetResource<GetMatchups>(`/matchups`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    team1_id: selectedOwnerId,
    team2_id: selectedOpponentId,
  });

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
      if (!selectedOwnerName) return;
      try {
        const response = await refetchH2HStandings();
        if (response?.data?.data) {
          console.log(response.data.data);
          const transformedData = response.data.data
            .filter((member) => member.owner_full_name === selectedOwnerName)
            .map((team) => ({
              ...team,
              opponent_full_name: team.opponent_full_name,
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
  }, [refetchH2HStandings, selectedOwnerName]);

  useEffect(() => {
    const fetchStatus = async () => {
      if (!selectedOwnerName || !selectedOpponentName) return;
      try {
        const response = await refetchH2HMatchups();
        if (response?.data?.data) {
          console.log(response);
          const transformedData = response.data.data.map((matchup) => {
            const ownerScore =
              matchup.team_a_member_id === selectedOwnerId ? matchup.team_a_score : matchup.team_b_score;

            const opponentScore =
              matchup.team_a_member_id === selectedOwnerId ? matchup.team_b_score : matchup.team_a_score;

            const ownerWon = matchup.winner === selectedOwnerId;

            return {
              ...matchup,
              season: matchup.season,
              week: matchup.week,
              result: `${ownerScore} - ${opponentScore}`,
              outcome: ownerWon ? 'W' : 'L',
            };
          });
          setScoresData(transformedData);
        }
      } catch (err) {
        console.error(err);
      }
    };

    void fetchStatus();
  }, [refetchH2HMatchups, selectedOwnerName, selectedOwnerId, selectedOpponentName]);

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
  const rowClassRules = {
    'cursor-pointer': 'true',
  };

  const standingsColumns = [
    { field: 'opponent_full_name' as keyof Team, headerName: 'Opponent', sortable: true },
    { field: 'games_played' as keyof Team, headerName: 'GP', sortable: true },
    { field: 'wins' as keyof Team, headerName: 'Wins', sortable: true },
    { field: 'losses' as keyof Team, headerName: 'Losses', sortable: true },
    {
      field: 'win_pct' as keyof Team,
      headerName: 'Win %',
      sortable: true,
      valueFormatter: (params: { value: number }) => (params.value != null ? params.value.toFixed(3) : ''),
      sort: DESC,
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

  const scoresColumns = [
    { field: 'season' as keyof Matchup, headerName: 'Season', sortable: true },
    { field: 'week' as keyof Matchup, headerName: 'Week' },
    { field: 'outcome' as keyof Matchup, headerName: 'Result', sortable: true },
    { field: 'result' as keyof Matchup, headerName: 'Score', sortable: true },
  ];

  return (
    <div className="space-y-4 my-4">
      <div className="flex items-center space-x-4">
        <label htmlFor="season" className="font-medium text-sm">
          League Member Name:
        </label>
        <Select onValueChange={setSelectedOwnerId} value={selectedOwnerId}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select a league member" />
          </SelectTrigger>
          <SelectContent>
            {members.length > 0 ? (
              members.map((member) => (
                <SelectItem key={member.member_id} value={member.member_id}>
                  {member.name}
                </SelectItem>
              ))
            ) : (
              <SelectItem disabled value="none">
                No league members found
              </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      {selectedOwnerName && standingsData ? (
        <>
          <div className="ag-theme-alpine" style={{ width: '100%' }}>
            <AgGridReact<Team>
              rowData={standingsData}
              columnDefs={standingsColumns}
              defaultColDef={{ resizable: true }}
              domLayout="autoHeight"
              rowClassRules={rowClassRules}
              onGridReady={onGridReady}
              onRowClicked={(event) => {
                const opponent = event.data?.opponent_full_name ?? null;
                setSelectedOpponentName(opponent);
              }}
            />
          </div>
          <Separator className="my-4" />
          {selectedOpponentId && (
            <div>
              <p className="mt-2 text-sm">
                Selected Opponent: <strong>{selectedOpponentName}</strong>
              </p>
              <AgGridReact<Matchup>
                rowData={scoresData}
                columnDefs={scoresColumns}
                defaultColDef={{ resizable: true }}
                domLayout="autoHeight"
                rowClassRules={rowClassRules}
                onGridReady={onGridReady}
              />
            </div>
          )}
        </>
      ) : (
        <p className="text-sm text-muted-foreground italic">
          Please select a league member to view their all-time head to head standings against the rest of the league.
        </p>
      )}
    </div>
  );
}

export default H2HStandings;
