import { useEffect, useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import type {
  GetLeagueMembers,
  GetSeasonStandings,
  GetMatchupsBetweenTeams,
  MatchupTableView,
  Member,
  StandingsSeason,
} from '@/features/standings/types';
import type { LeagueData } from '@/components/types/league_data';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { DataTable } from '@/components/utils/dataTable';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { SortableHeader } from '@/components/utils/sortableColumnHeader';
import { SeasonSelect } from '@/components/utils/SeasonSelect';

function SeasonStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  const [selectedSeason, setSelectedSeason] = useState<number | undefined>(undefined);
  const [standingsData, setStandingsData] = useState<StandingsSeason[]>([]);
  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined);
  const [scoresData, setScoresData] = useState<MatchupTableView[]>([]);
  const [expandedBoxScoreOpen, setExpandedBoxScoreOpen] = useState<boolean>(false);
  const [members, setMembers] = useState<Member[]>([]);
  const selectedOwnerId = members.find((m) => m.name === selectedOwnerName)?.member_id ?? undefined;
  const [H2HMatchupData, setH2HMatchupData] = useState<GetMatchupsBetweenTeams['data']>();

  const columns: ColumnDef<StandingsSeason>[] = [
    {
      accessorKey: 'owner_full_name',
      header: 'Owner',
      cell: ({ row }) => {
        const isSelected = row.original.owner_full_name === selectedOwnerName;
        const { playoff_status, championship_status } = row.original;

        let suffix = '';
        if (playoff_status === 'CLINCHED_FIRST_ROUND_BYE') {
          suffix = 'z';
        } else if (playoff_status === 'MADE_PLAYOFFS') {
          suffix = 'x';
        }

        const crown = championship_status ? ' 👑' : '';

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

  const { refetch: refetchSeasonStandings } = useGetResource<GetSeasonStandings['data']>(`/standings`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    standings_type: 'season',
    season: selectedSeason,
  });

  const { refetch: refetchLeagueMembers } = useGetResource<GetLeagueMembers['data']>(`/members`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
  });

  const { refetch: refetchSeasonMatchups } = useGetResource<GetMatchupsBetweenTeams['data']>(`/matchups`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    playoff_filter: 'exclude',
    team1_id: selectedOwnerId,
    season: selectedSeason,
  });

  const { refetch: refetchSeasonMatchup } = useGetResource<GetMatchupsBetweenTeams['data']>(`/matchups`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    playoff_filter: 'exclude',
    team1_id: selectedOwnerId,
    season: selectedSeason,
    week_number: selectedWeek,
  });

  useEffect(() => {
    if (!selectedSeason) return;
    const fetchStatus = async () => {
      try {
        const response = await refetchSeasonStandings();
        if (response?.data?.data) {
          console.log(response.data.data);
          const transformedData: StandingsSeason[] = response.data.data.map((team) => {
            const wins = Number(team.wins);
            const losses = Number(team.losses);
            const ties = Number(team.ties);
            return {
              ...team,
              record: `${wins}-${losses}-${ties}`,
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
        const response = await refetchSeasonMatchups();
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
  }, [refetchSeasonMatchups, selectedOwnerName, selectedOwnerId]);

  useEffect(() => {
    if (!selectedSeason || !selectedWeek) return;
    const fetchStatus = async () => {
      try {
        const response = await refetchSeasonMatchup();
        if (response.data?.data) {
          setH2HMatchupData(response.data?.data);
        }
      } catch (err) {
        console.error(err);
      }
    };
    void fetchStatus();
  }, [refetchSeasonMatchup, selectedSeason, selectedWeek, H2HMatchupData]);

  // Open matchup box score whenever season/week are selected
  useEffect(() => {
    if (selectedSeason && selectedWeek && H2HMatchupData && H2HMatchupData.length > 0) {
      setExpandedBoxScoreOpen(true);
    }
  }, [selectedSeason, selectedWeek, H2HMatchupData]);

  return (
    <div className="space-y-4 my-4 px-2">
      <SeasonSelect
        leagueData={leagueData}
        selectedSeason={selectedSeason ? String(selectedSeason) : undefined}
        onSeasonChange={(season) => {
          setSelectedOwnerName(null);
          setSelectedSeason(Number(season));
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
              { id: 'points_for_per_game', desc: true },
            ]}
          />
          <p className="text-sm text-muted-foreground italic mt-1">
            z = clinched a first round bye | x = clinched a playoff spot | 👑 = won the championship
          </p>
          <h1 className="font-semibold mt-6">Season Schedule for {selectedOwnerName}</h1>
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
          <DataTable
            columns={columns}
            data={standingsData}
            initialSorting={[
              { id: 'win_pct', desc: true },
              { id: 'points_for_per_game', desc: true },
            ]}
          />
          <p className="text-sm text-muted-foreground italic mt-1">
            z = clinched a first round bye | x = clinched a playoff spot | 👑 = won the championship
          </p>
        </div>
      )}
    </div>
  );
}

export default SeasonStandings;
