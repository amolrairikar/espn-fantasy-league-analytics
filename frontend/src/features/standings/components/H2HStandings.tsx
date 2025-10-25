import { useEffect, useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import type {
  GetH2HStandings,
  GetLeagueMembers,
  GetMatchups,
  Matchup,
  Member,
  StandingsH2H,
} from '@/features/standings/types';
import type { LeagueData } from '@/features/login/types';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import { useLocalStorage } from '@/components/hooks/useLocalStorage';
import { DataTable } from '@/components/utils/dataTable';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { SortableHeader } from '@/components/utils/sortableColumnHeader';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

function H2HStandings() {
  const [leagueData] = useLocalStorage<LeagueData>('leagueData', null);
  if (!leagueData || !leagueData.leagueId || !leagueData.platform) {
    throw new Error('Invalid league metadata: missing leagueId and/or platform.');
  }

  type memberConfig = { name: string; member_id: string };
  const [members, setMembers] = useState<memberConfig[]>([]);
  const [selectedOwnerId, setSelectedOwnerId] = useState<string | undefined>(undefined);
  const selectedOwnerName = members.find((m) => m.member_id === selectedOwnerId)?.name ?? null;
  const [selectedOpponentName, setSelectedOpponentName] = useState<string | null>(null);
  const selectedOpponentId = members.find((m) => m.name === selectedOpponentName)?.member_id ?? undefined;
  const [selectedSeason, setSelectedSeason] = useState<number | undefined>(undefined);
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined);
  const [standingsData, setStandingsData] = useState<StandingsH2H[]>([]);
  const [scoresData, setScoresData] = useState<Matchup[]>([]);
  const [H2HMatchupData, setH2HMatchupData] = useState<GetMatchups['data']>();
  const [expandedBoxScoreOpen, setExpandedBoxScoreOpen] = useState<boolean>(false);

  const columnsH2HStandings: ColumnDef<StandingsH2H>[] = [
    {
      accessorKey: 'opponent_full_name',
      header: 'Opponent',
      cell: ({ row }) => {
        const isSelected = row.original.opponent_full_name === selectedOpponentName;
        return (
          <div
            className={`cursor-pointer hover:bg-muted px-2 py-1 rounded transition 
                        ${isSelected ? 'outline-2 outline-ring' : ''}`}
            onClick={() => setSelectedOpponentName(row.original.opponent_full_name)}
          >
            {row.original.opponent_full_name}
          </div>
        );
      },
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
    setSelectedSeason: (season: number) => void,
    setSelectedWeek: (week: number) => void,
  ): ColumnDef<Matchup>[] => [
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

  const { refetch: refetchLeaguemembers } = useGetResource<GetLeagueMembers['data']>(`/members`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
  });

  const { refetch: refetchH2HStandings } = useGetResource<GetH2HStandings['data']>(`/standings`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    standings_type: 'h2h',
  });

  const { refetch: refetchH2HMatchups } = useGetResource<GetMatchups['data']>(`/matchups`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    team1_id: selectedOwnerId,
    team2_id: selectedOpponentId,
  });

  const { refetch: refetchH2HMatchup } = useGetResource<GetMatchups['data']>(`/matchups`, {
    league_id: leagueData.leagueId,
    platform: leagueData.platform,
    team1_id: selectedOwnerId,
    team2_id: selectedOpponentId,
    season: selectedSeason,
    week_number: selectedWeek,
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
            .map((team) => {
              const wins = Number(team.wins);
              const losses = Number(team.losses);
              return {
                ...team,
                opponent_full_name: team.opponent_full_name,
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
              season: Number(matchup.season),
              week: Number(matchup.week),
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

  // Reset opponent whenever the owner changes
  useEffect(() => {
    setSelectedOpponentName(null);
  }, [selectedOwnerId]);

  useEffect(() => {
    if (!selectedSeason || !selectedWeek) return;
    const fetchStatus = async () => {
      try {
        const response = await refetchH2HMatchup();
        if (response.data?.data) {
          setH2HMatchupData(response.data?.data);
        }
      } catch (err) {
        console.error(err);
      }
    };
    void fetchStatus();
  }, [refetchH2HMatchup, selectedSeason, selectedWeek, H2HMatchupData]);

  // Open matchup box score whenever season/week are selected
  useEffect(() => {
    if (selectedSeason && selectedWeek) {
      setExpandedBoxScoreOpen(true);
    }
  }, [selectedSeason, selectedWeek]);

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
          {!selectedOpponentId && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground italic mt-2">
                Please click on an opponent's name in the table to view a table of matchup results against them.
              </p>
              <h1 className="font-semibold">All-Time Standings vs. League Opponents</h1>
              <DataTable
                columns={columnsH2HStandings}
                data={standingsData}
                initialSorting={[{ id: 'win_pct', desc: true }]}
              />
            </div>
          )}

          {selectedOpponentId && (
            <div className="space-y-2">
              <h1 className="font-semibold">All-Time Standings vs. League Opponents</h1>
              <DataTable
                columns={columnsH2HStandings}
                data={standingsData}
                initialSorting={[{ id: 'win_pct', desc: true }]}
              />
              <h1 className="font-semibold mt-6">All-Time Matchup Results vs {selectedOpponentName}</h1>
              <p className="text-sm text-muted-foreground italic mt-2">
                Please click on a matchup to view the detailed box score.
              </p>
              <DataTable
                columns={columnsH2HMatchupTable}
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
