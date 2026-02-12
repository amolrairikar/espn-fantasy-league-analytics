import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { type ColumnDef } from '@tanstack/react-table';
import type { MatchupTableView, StandingsH2H } from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { DataTable } from '@/components/utils/dataTable';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { SortableHeader } from '@/components/utils/sortableColumnHeader';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { fetchH2HStandings } from '@/api/standings/api_calls';
import { fetchMatchups } from '@/api/matchups/api_calls';
import { useFetchLeagueOwners } from '@/components/hooks/fetchOwners';
import { StandingsTableSkeleton } from '@/features/standings/components/SkeletonStandingsTable';

function useFetchH2HStandings(
  league_id: string,
  platform: string,
  standings_type: string,
) {
  return useQuery({
    queryKey: ['h2h_standings', league_id, platform, standings_type],
    queryFn: () => fetchH2HStandings(
      league_id,
      platform,
      standings_type,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!standings_type, // only run if input args are available
  });
};

function useFetchMatchupsBetweenTeams(
  league_id: string,
  platform: string,
  playoff_filter: string,
  team1_id: string,
  team2_id: string,
) {
  return useQuery({
    queryKey: ['matchups_between_teams', league_id, platform, playoff_filter, team1_id, team2_id],
    queryFn: () => fetchMatchups(
      league_id,
      platform,
      playoff_filter,
      team1_id,
      team2_id,
      undefined, // week_number
      undefined, // season
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!playoff_filter && !!team1_id && !!team2_id, // only run if input args are available
  });
};

function useFetchSpecificMatchup(
  league_id: string,
  platform: string,
  playoff_filter: string,
  team1_id: string,
  team2_id: string,
  week_number: string,
  season: string,
) {
  return useQuery({
    queryKey: ['specified_matchup', league_id, platform, playoff_filter, team1_id, team2_id, week_number, season],
    queryFn: () => fetchMatchups(
      league_id,
      platform,
      playoff_filter,
      team1_id,
      team2_id,
      week_number,
      season,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!playoff_filter && !!team1_id && !!team2_id && !!week_number && !!season, // only run if input args are available
  });
};

function H2HStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);

  const { data: rawStandings, isLoading: loadingStandings } = useFetchH2HStandings(
    leagueData!.leagueId,
    leagueData!.platform,
    'h2h',
  );

  const { data: owners } = useFetchLeagueOwners(
    leagueData!.leagueId,
    leagueData!.platform
  );

  const [selectedOwnerId, setSelectedOwnerId] = useState<string | undefined>(undefined);
  const selectedOwnerName = owners?.data.find((m) => m.owner_id === selectedOwnerId)?.owner_full_name ?? null;
  const [selectedOpponentName, setSelectedOpponentName] = useState<string | null>(null);
  const selectedOpponentId = owners?.data.find((m) => m.owner_full_name === selectedOpponentName)?.owner_id ?? undefined;
  const [selectedSeason, setSelectedSeason] = useState<string | undefined>(undefined);
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined);
  const [expandedBoxScoreOpen, setExpandedBoxScoreOpen] = useState<boolean>(false);

  const { data: H2HMatchups, isLoading: loadingH2HMatchups } = useFetchMatchupsBetweenTeams(
    leagueData!.leagueId,
    leagueData!.platform,
    'exclude',
    selectedOwnerId!,
    selectedOpponentId!,
  )

  const { data: specifiedMatchup } = useFetchSpecificMatchup(
    leagueData!.leagueId,
    leagueData!.platform,
    'exclude',
    selectedOwnerId!,
    selectedOpponentId!,
    String(selectedWeek!),
    selectedSeason!,
  )

  const columnsH2HStandings: ColumnDef<StandingsH2H>[] = [
    {
      accessorKey: 'opponent_full_name',
      header: 'Opponent',
      cell: ({ row }) => <div className="px-2 py-1">{row.original.opponent_full_name}</div>,
    },
    {
      accessorKey: 'games_played',
      header: ({ column }) => (
        <div className="w-full text-center min-w-[90px]">
          <SortableHeader column={column} label="GP" />
        </div>
      ),
      cell: ({ row }) => <div className="text-center">{row.original.games_played}</div>,
      minSize: 90,
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

  const columnsH2HMatchups = (
    setSelectedSeason: (season: string) => void,
    setSelectedWeek: (week: number) => void,
  ): ColumnDef<MatchupTableView>[] => [
    {
      accessorKey: 'season',
      header: () => <div className="w-full text-center">Season</div>,
      cell: ({ row }) => (
        <div
          className="text-center cursor-pointer"
          onClick={() => {
            setSelectedSeason(row.original.season);
            setSelectedWeek(row.original.week);
          }}
        >
          {row.original.season}
        </div>
      ),
    },
    {
      accessorKey: 'week',
      header: () => <div className="w-full text-center">Week</div>,
      cell: ({ row }) => (
        <div
          className="text-center cursor-pointer"
          onClick={() => {
            setSelectedSeason(row.original.season);
            setSelectedWeek(row.original.week);
          }}
        >
          {row.original.week}
        </div>
      ),
    },
    {
      accessorKey: 'result',
      header: () => <div className="w-full text-center">Result</div>,
      cell: ({ row }) => <div className="text-center">{row.original.result}</div>,
    },
    {
      accessorKey: 'outcome',
      header: () => <div className="w-full text-center">Outcome</div>,
      cell: ({ row }) => <div className="text-center">{row.original.outcome}</div>,
    },
  ];

  const columnsH2HMatchupTable = columnsH2HMatchups(setSelectedSeason, setSelectedWeek);

  const standingsData = useMemo(() => {
    if (!rawStandings?.data || !selectedOwnerName) return [];

    return rawStandings.data
      .filter((member) => member.owner_full_name === selectedOwnerName)
      .map((team) => ({
        ...team,
        games_played: Number(team.games_played),
        record: `${team.wins}-${team.losses}-${team.ties}`,
        win_pct: parseFloat(team.win_pct),
        points_for_per_game: parseFloat(team.points_for_per_game),
        points_against_per_game: parseFloat(team.points_against_per_game),
      }));
  }, [rawStandings?.data, selectedOwnerName]);

  const scoresData = useMemo(() => {
    if (!H2HMatchups?.data) return [];

    return H2HMatchups.data.map((matchup) => {
      const isTeamA = matchup.team_a_owner_id === selectedOwnerId;
      const ownerScore = isTeamA ? matchup.team_a_score : matchup.team_b_score;
      const opponentScore = isTeamA ? matchup.team_b_score : matchup.team_a_score;
      const ownerWon = matchup.winner === selectedOwnerId;

      return {
        ...matchup,
        week: Number(matchup.week),
        result: `${ownerScore} - ${opponentScore}`,
        outcome: ownerWon ? 'W' : 'L',
      };
    });
  }, [H2HMatchups?.data, selectedOwnerId]);

  // Open matchup box score whenever season/week are selected
  useEffect(() => {
    if (selectedSeason && selectedWeek) {
      setExpandedBoxScoreOpen(true);
    }
  }, [selectedSeason, selectedWeek]);

  // Reset opponent whenever new owner is selected
  useEffect(() => {
    setSelectedOpponentName(null);
  }, [selectedOwnerName])

  return (
    <div className="space-y-4 my-4 px-4">
      <div className="flex items-center space-x-4">
        <label htmlFor="season" className="font-medium text-sm">
          League Member Name:
        </label>
        <Select onValueChange={setSelectedOwnerId} value={selectedOwnerId}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select a league member" />
          </SelectTrigger>
          <SelectContent>
            {owners!.data.length > 0 ? (
              owners!.data.map((owner) => (
                <SelectItem key={owner.owner_id} value={owner.owner_id}>
                  {owner.owner_full_name}
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
          {!selectedOpponentId && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground italic mt-2">
                Click on an opponent's name in the table to view a table of matchup results against them.
              </p>
              <h1 className="font-semibold">All-Time Standings vs. League Opponents</h1>
              {loadingStandings ? (
                <StandingsTableSkeleton />
              ) : (
                <DataTable
                  columns={columnsH2HStandings}
                  data={standingsData}
                  initialSorting={[{ id: 'win_pct', desc: true }]}
                  onRowClick={(row) => setSelectedOpponentName(row.opponent_full_name)}
                  selectedRow={standingsData.find(team => team.opponent_full_name === selectedOpponentName) ?? null}
                />
              )}
            </div>
          )}

          {selectedOpponentId && (
            <div className="space-y-2">
              <h1 className="font-semibold">All-Time Standings vs. League Opponents</h1>
              {loadingStandings ? (
                <StandingsTableSkeleton />
              ) : (
                <DataTable
                  columns={columnsH2HStandings}
                  data={standingsData}
                  initialSorting={[{ id: 'win_pct', desc: true }]}
                  onRowClick={(row) => setSelectedOpponentName(row.opponent_full_name)}
                  selectedRow={standingsData.find(team => team.opponent_full_name === selectedOpponentName) ?? null}
                />
              )}
              <h1 className="font-semibold mt-6">All-Time Matchup Results vs {selectedOpponentName}</h1>
              <p className="text-sm text-muted-foreground italic mt-2">
                Click on a matchup to view the detailed box score.
              </p>
              {loadingH2HMatchups ? (
                <StandingsTableSkeleton />
              ) : (
                <DataTable
                  columns={columnsH2HMatchupTable}
                  data={scoresData}
                  initialSorting={[
                    { id: 'season', desc: false },
                    { id: 'week', desc: false },
                  ]}
                  onRowClick={(row) => {
                    setSelectedSeason(row.season);
                    setSelectedWeek(row.week);
                  }}
                  selectedRow={scoresData.find(
                    (matchup) =>
                      matchup.season === selectedSeason && matchup.week === selectedWeek,
                  ) ?? null}
                />
              )}

              {selectedSeason && selectedWeek && H2HMatchups && H2HMatchups.data.length > 0 && (
                <MatchupSheet
                  matchup={specifiedMatchup!.data[0]}
                  open={expandedBoxScoreOpen}
                  onClose={() => {
                    setSelectedSeason(undefined);
                    setSelectedWeek(undefined);
                  }}
                />
              )}
            </div>
          )}
        </>
      ) : (
        <p className="text-sm text-muted-foreground italic">
          Select a league member to view their all-time head to head standings against the rest of the league.
        </p>
      )}
    </div>
  );
}

export default H2HStandings;
