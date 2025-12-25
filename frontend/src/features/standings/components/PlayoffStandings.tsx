import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { type ColumnDef } from '@tanstack/react-table';
import type { MatchupTableView, StandingsAllTime } from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import { DataTable } from '@/components/utils/dataTable';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { SortableHeader } from '@/components/utils/sortableColumnHeader';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { fetchPlayoffStandings } from '@/api/standings/api_calls';
import { fetchMatchups } from '@/api/matchups/api_calls';
import { useFetchLeagueOwners } from '@/components/hooks/fetchOwners';
import { StandingsTableSkeleton } from '@/features/standings/components/SkeletonStandingsTable';

function useFetchPlayoffStandings(
  league_id: string,
  platform: string,
  standings_type: string,
) {
  return useQuery({
    queryKey: ['playoff_standings', league_id, platform, standings_type],
    queryFn: () => fetchPlayoffStandings(
      league_id,
      platform,
      standings_type,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!standings_type, // only run if input args are available
  });
};

function useFetchPlayoffMatchupsForTeam(
  league_id: string,
  platform: string,
  playoff_filter: string,
  team1_id: string,
) {
  return useQuery({
    queryKey: ['single_team_playoff_matchups', league_id, platform, playoff_filter, team1_id],
    queryFn: () => fetchMatchups(
      league_id,
      platform,
      playoff_filter,
      team1_id,
      undefined, // team2_id
      undefined, // week_number
      undefined, // season
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!playoff_filter && !!team1_id, // only run if input args are available
  });
};

function useFetchSpecificPlayoffMatchup(
  league_id: string,
  platform: string,
  playoff_filter: string,
  team1_id: string,
  week_number: string,
  season: string,
) {
  return useQuery({
    queryKey: ['specified_playoff_matchup', league_id, platform, playoff_filter, team1_id, week_number, season],
    queryFn: () => fetchMatchups(
      league_id,
      platform,
      playoff_filter,
      team1_id,
      undefined, // team2_id
      week_number,
      season,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!playoff_filter && !!team1_id && !!week_number && !!season, // only run if input args are available
  });
};

function PlayoffStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);

  const { data: rawStandings, isLoading: loadingStandings } = useFetchPlayoffStandings(
    leagueData!.leagueId,
    leagueData!.platform,
    'playoffs',
  );

  const { data: owners } = useFetchLeagueOwners(
    leagueData!.leagueId,
    leagueData!.platform
  );

  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);
  const selectedOwnerId = owners?.data.find((m) => m.owner_full_name === selectedOwnerName)?.owner_id ?? undefined;
  const [selectedSeason, setSelectedSeason] = useState<string | undefined>(undefined);
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined);
  const [expandedBoxScoreOpen, setExpandedBoxScoreOpen] = useState<boolean>(false);

  const { data: PlayoffMatchups, isLoading: loadingPlayoffMatchups } = useFetchPlayoffMatchupsForTeam(
    leagueData!.leagueId,
    leagueData!.platform,
    'only',
    selectedOwnerId!,
  )

  const { data: specifiedMatchup } = useFetchSpecificPlayoffMatchup(
    leagueData!.leagueId,
    leagueData!.platform,
    'include',
    selectedOwnerId!,
    String(selectedWeek!),
    selectedSeason!,
  )

  // Early return if saving league data to local storage fails
  if (!leagueData) {
    return (
      <p>
        League credentials not found in local browser storage. Please try logging in again and if the issue persists,
        create a support ticket.
      </p>
    );
  };

  const columns: ColumnDef<StandingsAllTime>[] = [
    {
      accessorKey: 'owner_full_name',
      header: 'Owner',
      cell: ({ row }) => <div className="px-2 py-1">{row.original.owner_full_name}</div>,
    },
    {
      accessorKey: 'games_played',
      header: ({ column }) => (
        <div className="w-full text-center min-w-[100px]">
          <SortableHeader column={column} label="GP" />
        </div>
      ),
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
      accessorKey: 'opponent_full_name',
      header: () => <div className="w-full text-center">Opponent</div>,
      cell: ({ row }) => <div className="text-center">{row.original.opponent_full_name}</div>,
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

  const standingsData = useMemo(() => {
    if (!rawStandings?.data) return [];
    
    return rawStandings.data.map((team) => ({
      ...team,
      games_played: Number(team.games_played),
      record: `${team.wins}-${team.losses}`,
      win_pct: parseFloat(team.win_pct),
      points_for_per_game: parseFloat(team.points_for_per_game),
      points_against_per_game: parseFloat(team.points_against_per_game),
    }));
  }, [rawStandings?.data]);

  const scoresData = useMemo(() => {
    if (!PlayoffMatchups?.data || !selectedOwnerId) return [];

    return PlayoffMatchups.data.map((matchup) => {
      const isTeamA = matchup.team_a_owner_id === selectedOwnerId;
      const ownerScore = isTeamA ? matchup.team_a_score : matchup.team_b_score;
      const opponentScore = isTeamA ? matchup.team_b_score : matchup.team_a_score;
      const opponentName = isTeamA ? matchup.team_b_owner_full_name : matchup.team_a_owner_full_name;
      const ownerWon = matchup.winner === selectedOwnerId;

      return {
        ...matchup,
        week: Number(matchup.week),
        opponent_full_name: opponentName,
        result: `${ownerScore} - ${opponentScore}`,
        outcome: ownerWon ? 'W' : 'L',
      };
    });
  }, [PlayoffMatchups?.data, selectedOwnerId]);

  // Open matchup box score whenever season/week are selected
  useEffect(() => {
    if (selectedSeason && selectedWeek) {
      setExpandedBoxScoreOpen(true);
    }
  }, [selectedSeason, selectedWeek]);

  return (
    <div className="space-y-4 my-4 px-4">
      <h1 className="font-semibold">Playoff Standings</h1>
      {selectedOwnerName ? (
        <div className="space-y-2">
          <DataTable
            columns={columns}
            data={standingsData}
            initialSorting={[{ id: 'win_pct', desc: true }]}
            onRowClick={(row) => setSelectedOwnerName(row.owner_full_name)}
            selectedRow={standingsData.find(team => team.owner_full_name === selectedOwnerName) ?? null}
          />
          <h1 className="font-semibold mt-6">All-Time Playoff Results for {selectedOwnerName}</h1>
          <p className="text-sm text-muted-foreground italic mt-2">
            Click on a matchup to view the detailed box score.
          </p>
          {loadingPlayoffMatchups ? (
            <StandingsTableSkeleton />
          ) : (
            <DataTable
              columns={columnsH2HMatchups(setSelectedSeason, setSelectedWeek)}
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
          {selectedSeason && selectedWeek && specifiedMatchup && specifiedMatchup.data.length > 0 && (
            <MatchupSheet
              matchup={specifiedMatchup.data[0]}
              open={expandedBoxScoreOpen}
              onClose={() => {
                setSelectedSeason(undefined);
                setSelectedWeek(undefined);
              }}
            />
          )}
        </div>
      ) : (
        <div className="space-y-4 my-4">
          <p className="text-sm text-muted-foreground italic">
            Click on an owner's name to display a table with all their playoff matchups.
          </p>
          {loadingStandings ? (
            <StandingsTableSkeleton />
          ) : (
            <DataTable
              columns={columns}
              data={standingsData}
              initialSorting={[{ id: 'win_pct', desc: true }]}
              onRowClick={(row) => setSelectedOwnerName(row.owner_full_name)}
              selectedRow={standingsData.find(team => team.owner_full_name === selectedOwnerName) ?? null}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default PlayoffStandings;
