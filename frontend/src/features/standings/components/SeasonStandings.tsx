import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { type ColumnDef } from '@tanstack/react-table';
import type { MatchupTableView, StandingsSeason } from '@/features/standings/types';
import type { LeagueData } from '@/components/types/league_data';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { DataTable } from '@/components/utils/dataTable';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { SortableHeader } from '@/components/utils/sortableColumnHeader';
import { SeasonSelect } from '@/components/utils/SeasonSelect';
import { fetchSingleSeasonStandings } from '@/api/standings/api_calls';
import { fetchMatchups } from '@/api/matchups/api_calls';
import { useFetchLeagueOwners } from '@/components/hooks/fetchOwners';
import { StandingsTableSkeleton } from '@/features/standings/components/SkeletonStandingsTable';

function useFetchSingleSeasonStandings(
  league_id: string,
  platform: string,
  standings_type: string,
  season: string,
) {
  return useQuery({
    queryKey: ['single_season_standings', league_id, platform, standings_type, season],
    queryFn: () => fetchSingleSeasonStandings(
      league_id,
      platform,
      standings_type,
      season,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!standings_type && !!season, // only run if input args are available
  });
};

function useFetchSeasonMatchupsForOneTeam(
  league_id: string,
  platform: string,
  playoff_filter: string,
  team1_id: string,
  season: string,
) {
  return useQuery({
    queryKey: ['season_matchups_one_team', league_id, platform, playoff_filter, team1_id, season],
    queryFn: () => fetchMatchups(
      league_id,
      platform,
      playoff_filter,
      team1_id,
      undefined, // team2_id
      undefined, // week_number
      season,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform && !!playoff_filter && !!team1_id && !!season, // only run if input args are available
  });
};

function useFetchSpecificMatchup(
  league_id: string,
  platform: string,
  playoff_filter: string,
  team1_id: string,
  week_number: string,
  season: string,
) {
  return useQuery({
    queryKey: ['specified_matchup', league_id, platform, playoff_filter, team1_id, week_number, season],
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

function SeasonStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);

  const [selectedSeason, setSelectedSeason] = useState<string | undefined>(undefined);
  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined);
  const [expandedBoxScoreOpen, setExpandedBoxScoreOpen] = useState<boolean>(false);

  const { data: rawStandings, isLoading: loadingStandings } = useFetchSingleSeasonStandings(
    leagueData!.leagueId,
    leagueData!.platform,
    'season',
    selectedSeason!,
  );

  const { data: owners } = useFetchLeagueOwners(
    leagueData!.leagueId,
    leagueData!.platform
  );

  const selectedOwnerId = owners?.data.find((m) => m.owner_full_name === selectedOwnerName)?.owner_id ?? undefined;

  const { data: seasonMatchups, isLoading: loadingSeasonMatchups } = useFetchSeasonMatchupsForOneTeam(
    leagueData!.leagueId,
    leagueData!.platform,
    'exclude',
    selectedOwnerId!,
    selectedSeason!,
  )

  const { data: specifiedMatchup } = useFetchSpecificMatchup(
    leagueData!.leagueId,
    leagueData!.platform,
    'exclude',
    selectedOwnerId!,
    String(selectedWeek!),
    selectedSeason!,
  )

  const columns: ColumnDef<StandingsSeason>[] = [
    {
      accessorKey: 'owner_full_name',
      header: 'Owner',
      cell: ({ row }) => {
        const isSelected = row.original.owner_full_name === selectedOwnerName;
        const { playoff_status, championship_status } = row.original;
        const crown = championship_status ? ' 👑' : '';

        let suffix = '';
        if (playoff_status === 'CLINCHED_FIRST_ROUND_BYE') {
          suffix = 'z';
        } else if (playoff_status === 'MADE_PLAYOFFS') {
          suffix = 'x';
        }

        return (
          <div
            className={`cursor-pointer hover:bg-muted px-2 py-1 rounded transition 
                        ${isSelected ? 'outline-2 outline-ring' : ''}`}
            onClick={() => setSelectedOwnerName(row.original.owner_full_name)}
          >
            {row.original.owner_full_name}
            {suffix && <span className="ml-3 lowercase font-semibold text-muted-foreground">{suffix}</span>}
            {crown && <span className="ml-2">{crown}</span>}
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
      accessorKey: 'points_for',
      header: ({ column }) => (
        <div className="w-full text-center min-w-[130px]">
          <SortableHeader column={column} label="Points For" />
        </div>
      ),
      cell: ({ row }) => <div className="text-center">{row.original.points_for.toFixed(2)}</div>,
      minSize: 130,
    },
    {
      accessorKey: 'points_against',
      header: ({ column }) => (
        <div className="w-full text-center min-w-[130px]">
          <SortableHeader column={column} label="Points Against" />
        </div>
      ),
      cell: ({ row }) => <div className="text-center">{row.original.points_against.toFixed(2)}</div>,
      minSize: 130,
    },
    {
      accessorKey: 'points_differential',
      header: ({ column }) => (
        <div className="w-full text-center min-w-[130px]">
          <SortableHeader column={column} label="Differential" />
        </div>
      ),
      cell: ({ row }) => {
        const value = row.original.points_differential;

        const formattedValue =
          value > 0 ? `+${value.toFixed(2)}` : value.toFixed(2);

        const colorClass =
          value > 0
            ? 'text-green-600'
            : value < 0
            ? 'text-red-600'
            : 'text-gray-900';

        return (
          <div className={`text-center ${colorClass}`}>
            {formattedValue}
          </div>
        );
      },
      minSize: 130,
    },
    {
      accessorKey: 'record_vs_league',
      header: () => <div className="w-full text-center">Record vs. League</div>,
      cell: ({ row }) => <div className="text-center">{row.original.record_vs_league}</div>,
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
      record: `${team.wins}-${team.losses}-${team.ties}`,
      win_pct: parseFloat(team.win_pct),
      points_for: parseFloat(team.points_for),
      points_against: parseFloat(team.points_against),
      points_differential: parseFloat(team.points_differential),
      record_vs_league: `${team.all_play_wins}-${team.all_play_losses}`
    }));
  }, [rawStandings]);

  const scoresData = useMemo(() => {
    if (!seasonMatchups?.data || !selectedOwnerId) return [];
    return seasonMatchups.data.map((matchup) => {
      const isTeamA = matchup.team_a_owner_id === selectedOwnerId;
      const ownerScore = isTeamA ? matchup.team_a_score : matchup.team_b_score;
      const opponentScore = isTeamA ? matchup.team_b_score : matchup.team_a_score;
      const opponentName = isTeamA ? matchup.team_b_owner_full_name : matchup.team_a_owner_full_name;
      const ownerWon = matchup.winner === selectedOwnerId;

      return {
        ...matchup,
        season: matchup.season,
        week: Number(matchup.week),
        opponent_full_name: opponentName,
        result: `${ownerScore} - ${opponentScore}`,
        outcome: ownerWon ? 'W' : 'L',
      };
    });
  }, [seasonMatchups, selectedOwnerId]);

  useEffect(() => {
    if (selectedSeason && selectedWeek && specifiedMatchup?.data && specifiedMatchup.data.length > 0) {
      setExpandedBoxScoreOpen(true);
    }
  }, [selectedSeason, selectedWeek, specifiedMatchup]);

  return (
    <div className="space-y-4 my-4 px-2">
      <SeasonSelect
        leagueData={leagueData!}
        selectedSeason={selectedSeason ? String(selectedSeason) : undefined}
        onSeasonChange={(season) => {
          setSelectedOwnerName(null);
          setSelectedSeason(season);
        }}
        className="px-2"
      />
      {selectedOwnerName ? (
        <div className="space-y-4 my-4 px-2">
          <DataTable
            columns={columns}
            data={standingsData}
            initialSorting={[
              { id: 'win_pct', desc: true },
              { id: 'points_for', desc: true },
            ]}
            selectedRow={standingsData.find(team => team.owner_full_name === selectedOwnerName) ?? null}
            onRowClick={(row) => setSelectedOwnerName(row.owner_full_name)}
          />
          <p className="text-sm text-muted-foreground italic mt-1">
            z = first round bye | x = playoffs | 👑 = won the championship
            <br />
            Note that playoff qualification status cannot be determined until the end of the season due to ESPN API limitations.
          </p>
          <h1 className="font-semibold mt-6">Season Schedule for {selectedOwnerName}</h1>
          {loadingSeasonMatchups ? (
            <StandingsTableSkeleton />
          ) : (
            <DataTable
              columns={columnsH2HMatchups(setSelectedSeason, setSelectedWeek)}
              data={scoresData}
              initialSorting={[
                { id: 'season', desc: false },
                { id: 'week', desc: false },
              ]}
              selectedRow={
                selectedSeason && selectedWeek
                  ? scoresData.find(
                      (matchup) =>
                        matchup.season === selectedSeason && matchup.week === selectedWeek,
                    ) ?? null
                  : null
              }
              onRowClick={(row) => {
                setSelectedSeason(row.season);
                setSelectedWeek(row.week);
              }}
            />
          )}
          {selectedSeason && selectedWeek && specifiedMatchup && specifiedMatchup.data.length > 0 && (
            <MatchupSheet
              matchup={specifiedMatchup.data[0]}
              open={expandedBoxScoreOpen}
              onClose={() => {
                setSelectedWeek(undefined);
              }}
            />
          )}
        </div>
      ) : (
        <div className="space-y-4 my-4 px-2">
          <p className="text-sm text-muted-foreground italic">
            Click on an owner's name to display a table with their regular season schedule results
          </p>
          {loadingStandings ? (
            <StandingsTableSkeleton />
          ) : (
            <DataTable
              columns={columns}
              data={standingsData}
              initialSorting={[
                { id: 'win_pct', desc: true },
                { id: 'points_for_per_game', desc: true },
              ]}
              selectedRow={standingsData.find(team => team.owner_full_name === selectedOwnerName) ?? null}
              onRowClick={(row) => setSelectedOwnerName(row.owner_full_name)}
            />
          )}
          <p className="text-sm text-muted-foreground italic mt-1">
            z = first round bye | x = playoffs | 👑 = won the championship
            <br />
            Note that playoff qualification status cannot be determined until the end of the season due to ESPN API limitations.
          </p>
        </div>
      )}
    </div>
  );
}

export default SeasonStandings;
