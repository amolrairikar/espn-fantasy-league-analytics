import { useEffect, useMemo, useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import { useDatabase } from '@/components/utils/DatabaseContext';
import { useDuckDbQuery } from '@/components/hooks/useDuckDbQuery';
import { DataTable } from '@/components/utils/dataTable';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import type { AllTimeStandingsData, MatchupTableView } from '@/features/standings/types';
import type { Matchup } from '@/features/scores/types';
import { StandingsTableSkeleton } from '@/features/standings/components/SkeletonStandingsTable';
import { getOutcomeByOwner } from '@/features/standings/utils';

function PlayoffStandings() {
  const { db } = useDatabase();
  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);
  const [selectedSeason, setSelectedSeason] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
  const [expandedBoxScoreOpen, setExpandedBoxScoreOpen] = useState<boolean>(false);

  const { data: standings, error: standingsQueryError, loading: loadingStandings } = useDuckDbQuery<any>(
    db,
    `
    SELECT * FROM league_playoff_standings ORDER BY wins DESC;
    `
  );

  const selectedOwnerId = standings?.find(s => s.owner_name === selectedOwnerName)?.owner_id;

  const { data: scores, error: scoresQueryError, loading: loadingScores } = useDuckDbQuery<any>(
    db,
    `
    SELECT *
    FROM league_matchups
    WHERE (home_team_owner_id = '${selectedOwnerId}' OR away_team_owner_id = '${selectedOwnerId}')
    AND playoff_tier_type = 'WINNERS_BRACKET';
    `
  );

  const scoresProcessed = useMemo(() => {
    if (!scores || !selectedOwnerId) return [];
    return scores.map((matchup) => {
      // Determine if the selected owner is the Home or Away team
      const isHome = matchup.home_team_owner_id === selectedOwnerId;

      const ownerScore = isHome ? matchup.home_team_score : matchup.away_team_score;
      const opponentScore = isHome ? matchup.away_team_score : matchup.home_team_score;
      const opponentName = isHome ? matchup.away_team_full_name : matchup.home_team_full_name;

      const outcome = getOutcomeByOwner(matchup, selectedOwnerId)

      return {
        ...matchup,
        season: matchup.season,
        week: Number(matchup.week),
        opponent_full_name: opponentName,
        result: `${ownerScore} - ${opponentScore}`,
        outcome: outcome,
      };
    });
  }, [scores, selectedOwnerId]);

  const { data: matchup, error: matchupQueryError } = useDuckDbQuery<Matchup>(
      selectedSeason && selectedWeek && selectedOwnerName ? db: null,
      `
      SELECT *
      FROM league_matchups
      WHERE season = '${selectedSeason}'
      AND week = '${selectedWeek}'
      AND (home_team_owner_id = '${selectedOwnerId}' OR away_team_owner_id = '${selectedOwnerId}')
      `
    );
    console.log(matchup);
  
    const activeMatchup = useMemo(() => {
    if (!matchup || !selectedSeason || !selectedWeek) return null;
      return matchup.find(m => 
        String(m.season) === String(selectedSeason) && 
        Number(m.week) === Number(selectedWeek)
      );
    }, [matchup, selectedSeason, selectedWeek]);
  
    useEffect(() => {
      if (selectedSeason && selectedWeek && matchup) {
        setExpandedBoxScoreOpen(true);
      }
    }, [selectedSeason, selectedWeek, matchup]);

  const columns: ColumnDef<AllTimeStandingsData>[] = [
    {
      accessorKey: 'owner_full_name',
      header: 'Owner',
      cell: ({ row }) => <div className="px-2 py-1">{row.original.owner_name}</div>,
    },
    {
      accessorKey: 'games_played',
      header: () => <div className="w-full text-center">GP</div>,
      cell: ({ row }) => <div className="text-center">{row.original.games_played}</div>,
    },
    {
      accessorKey: 'record',
      header: () => <div className="w-full text-center">Record</div>,
      cell: ({ row }) => <div className="text-center">{row.original.record}</div>,
    },
    {
      accessorKey: 'win_pct',
      header: () => <div className="w-full text-center">Win %</div>,
      cell: ({ row }) => <div className="text-center">{row.original.win_pct.toFixed(3)}</div>,
      minSize: 100,
    },
    {
      accessorKey: 'points_for_per_game',
      header: () => <div className="w-full text-center">PF/Game</div>,
      cell: ({ row }) => <div className="text-center">{row.original.avg_pf.toFixed(1)}</div>,
      minSize: 130,
    },
    {
      accessorKey: 'points_against_per_game',
      header: () => <div className="w-full text-center">PA/Game</div>,
      cell: ({ row }) => <div className="text-center">{row.original.avg_pa.toFixed(1)}</div>,
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

  const isLoading = (loadingStandings || loadingScores);
  const activeError = (standingsQueryError || scoresQueryError || matchupQueryError);

  if (isLoading) return <StandingsTableSkeleton/>;
  
  if (activeError) return (
    <div className="p-8 text-center text-red-500">
      <h2>Error loading league data</h2>
      <p>{activeError instanceof Error ? activeError.message : activeError}</p>
    </div>
  )

  return(
    <div className="space-y-4 my-4 px-2">
      <DataTable
        columns={columns}
        data={standings || []}
        initialSorting={[{ id: 'win_pct', desc: true }]}
        selectedRow={standings!.find(team => team.owner_name === selectedOwnerName) ?? null}
        onRowClick={(row) => setSelectedOwnerName(row.owner_name)}
      />
      <MatchupSheet
        matchup={activeMatchup!}
        open={expandedBoxScoreOpen && !!activeMatchup}
        onClose={() => {
          setSelectedWeek(null);
          setExpandedBoxScoreOpen(false);
      }}
      />
      {selectedOwnerName ? (
        <>
          <DataTable
            columns={columnsH2HMatchups(setSelectedSeason, setSelectedWeek)}
            data={scoresProcessed || []}
            initialSorting={[
              { id: 'season', desc: false },
              { id: 'week', desc: false },
            ]}
            selectedRow={
            selectedSeason && selectedWeek
              ? scores!.find((matchup) => matchup.season === selectedSeason && matchup.week === selectedWeek) ?? null
              : null
            }
            onRowClick={(row) => {
              setSelectedSeason(row.season);
              setSelectedWeek(row.week);
            }}
          />
        </>
      ) : (
        <></>
      )}
    </div>
  )
}

export default PlayoffStandings;