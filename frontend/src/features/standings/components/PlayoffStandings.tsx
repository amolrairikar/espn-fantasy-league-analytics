import { useEffect, useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import type {
  GetAllTimeStandings,
  GetLeagueMembers,
  GetMatchupsBetweenTeams,
  MatchupTableView,
  Member,
  StandingsAllTime,
} from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import { DataTable } from '@/components/utils/dataTable';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { SortableHeader } from '@/components/utils/sortableColumnHeader';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';

function PlayoffStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const [standingsData, setStandingsData] = useState<StandingsAllTime[]>([]);
  const [scoresData, setScoresData] = useState<MatchupTableView[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);
  const selectedOwnerId = members.find((m) => m.name === selectedOwnerName)?.member_id ?? undefined;
  const [selectedSeason, setSelectedSeason] = useState<number | undefined>(undefined);
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined);
  const [H2HMatchupData, setH2HMatchupData] = useState<GetMatchupsBetweenTeams['data']>();
  const [expandedBoxScoreOpen, setExpandedBoxScoreOpen] = useState<boolean>(false);

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
    setSelectedSeason: (season: number) => void,
    setSelectedWeek: (week: number) => void,
  ): ColumnDef<MatchupTableView>[] => [
    {
      accessorKey: 'season',
      header: () => <div className="w-full text-center">Season</div>,
      cell: ({ row }) => (
        <div
          className="text-center cursor-pointer hover:underline"
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
          className="text-center cursor-pointer hover:underline"
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

  const { refetch: refetchPlayoffStandings } = useGetResource<GetAllTimeStandings['data']>(`/standings`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    standings_type: 'playoffs',
  });

  const { refetch: refetchLeagueMembers } = useGetResource<GetLeagueMembers['data']>(`/members`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
  });

  const { refetch: refetchPlayoffMatchups } = useGetResource<GetMatchupsBetweenTeams['data']>(`/matchups`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    playoff_filter: 'only',
    team1_id: selectedOwnerId,
  });

  const { refetch: refetchPlayoffMatchup } = useGetResource<GetMatchupsBetweenTeams['data']>(`/matchups`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    playoff_filter: 'include',
    team1_id: selectedOwnerId,
    season: selectedSeason,
    week_number: selectedWeek,
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchPlayoffStandings();
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
  }, [refetchPlayoffStandings]);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await refetchLeagueMembers();
        if (response.data?.data) {
          const membersData = response.data?.data;
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
  }, [refetchLeagueMembers]);

  useEffect(() => {
    const fetchStatus = async () => {
      if (!selectedOwnerName) return;
      try {
        const response = await refetchPlayoffMatchups();
        if (response?.data?.data) {
          console.log(response);
          const transformedData = response.data.data.map((matchup) => {
            const ownerScore =
              matchup.team_a_member_id === selectedOwnerId ? matchup.team_a_score : matchup.team_b_score;
            const opponentScore =
              matchup.team_a_member_id === selectedOwnerId ? matchup.team_b_score : matchup.team_a_score;
            const opponentName =
              matchup.team_a_member_id === selectedOwnerId ? matchup.team_b_full_name : matchup.team_a_full_name;
            const ownerWon = matchup.winner === selectedOwnerId;

            return {
              ...matchup,
              season: Number(matchup.season),
              week: Number(matchup.week),
              opponent_full_name: opponentName,
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
  }, [refetchPlayoffMatchups, selectedOwnerName, selectedOwnerId]);

  useEffect(() => {
    if (!selectedSeason || !selectedWeek) return;
    const fetchStatus = async () => {
      try {
        const response = await refetchPlayoffMatchup();
        if (response.data?.data) {
          setH2HMatchupData(response.data?.data);
        }
      } catch (err) {
        console.error(err);
      }
    };
    void fetchStatus();
  }, [refetchPlayoffMatchup, selectedSeason, selectedWeek, H2HMatchupData]);

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
          <DataTable columns={columns} data={standingsData} initialSorting={[{ id: 'games_played', desc: true }]} />
          <h1 className="font-semibold mt-6">All-Time Playoff Results for {selectedOwnerName}</h1>
          <p className="text-sm text-muted-foreground italic mt-2">
            Click on a matchup to view the detailed box score.
          </p>
          <DataTable
            columns={columnsH2HMatchups(setSelectedSeason, setSelectedWeek)}
            data={scoresData}
            initialSorting={[
              { id: 'season', desc: false },
              { id: 'week', desc: false },
            ]}
          />
          {selectedSeason && selectedWeek && H2HMatchupData && H2HMatchupData.length > 0 && (
            <MatchupSheet
              matchup={H2HMatchupData[0]}
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
          <DataTable columns={columns} data={standingsData} initialSorting={[{ id: 'games_played', desc: true }]} />
        </div>
      )}
    </div>
  );
}

export default PlayoffStandings;
