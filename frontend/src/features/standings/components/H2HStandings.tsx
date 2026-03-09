import { useEffect, useMemo, useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import { useDatabase } from '@/components/utils/DatabaseContext';
import { useDuckDbQuery } from '@/components/hooks/useDuckDbQuery';
import { DataTable } from '@/components/utils/dataTable';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { CustomSelect } from '@/components/utils/CustomSelectbox';
import type { MatchupTableView, H2HStandingsData } from '@/features/standings/types';
import type { Matchup } from '@/features/scores/types';
import { StandingsTableSkeleton } from '@/features/standings/components/SkeletonStandingsTable';
import { getOutcomeByOwner } from '@/features/standings/utils';

function H2HStandings() {
  const { db } = useDatabase();
  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);
  const [selectedOpponentName, setSelectedOpponentName] = useState<string | null>(null);
  const [selectedSeason, setSelectedSeason] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
  const [expandedBoxScoreOpen, setExpandedBoxScoreOpen] = useState<boolean>(false);

  const { data: owners, error: ownersQueryError, loading: loadingOwners } = useDuckDbQuery<any>(
    db,
    `
    SELECT
      owner_id,
      MAX(owner_full_name) AS owner_full_name
    FROM league_members
    GROUP BY owner_id;
    `
  );
  const members = owners ? owners.map(row => row.owner_full_name) : [];
  const selectedOwnerId = owners?.find(s => s.owner_full_name === selectedOwnerName)?.owner_id;
  const selectedOpponentId = owners?.find(s => s.owner_full_name === selectedOpponentName)?.owner_id;

  const { data: standings, error: standingsQueryError } = useDuckDbQuery<any>(
    selectedOwnerId ? db: null,
    `
    SELECT *
    FROM league_h2h_standings
    WHERE owner_id = '${selectedOwnerId}';
    `
  );

  const { data: matchups, error: matchupsQueryError } = useDuckDbQuery<any>(
    selectedOwnerId && selectedOpponentId ? db: null,
    `
    SELECT *
    FROM league_matchups
    WHERE (home_team_owner_id = '${selectedOwnerId}' OR away_team_owner_id = '${selectedOwnerId}')
    AND (home_team_owner_id = '${selectedOpponentId}' OR away_team_owner_id = '${selectedOpponentId}')
    AND playoff_tier_type = 'NONE';
    `
  );

  const scoresProcessed = useMemo(() => {
    if (!matchups || !selectedOwnerId || !selectedOpponentId) return [];
    return matchups.map((matchup) => {
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
  }, [matchups, selectedOwnerId, selectedOpponentId]);

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

  const { data: h2hMatchup, error: h2hMatchupQueryError } = useDuckDbQuery<Matchup>(
    selectedSeason && selectedWeek && selectedOwnerName ? db: null,
    `
    SELECT *
    FROM league_matchups
    WHERE season = '${selectedSeason}'
    AND week = '${selectedWeek}'
    AND (home_team_full_name = '${selectedOwnerName}' OR away_team_full_name = '${selectedOwnerName}')
    `
  );

  const activeMatchup = useMemo(() => {
  if (!h2hMatchup || !selectedSeason || !selectedWeek) return null;
    return h2hMatchup.find(m => 
      String(m.season) === String(selectedSeason) && 
      Number(m.week) === Number(selectedWeek)
    );
  }, [h2hMatchup, selectedSeason, selectedWeek]);

  useEffect(() => {
    if (selectedSeason && selectedWeek && h2hMatchup) {
      setExpandedBoxScoreOpen(true);
    }
  }, [selectedSeason, selectedWeek, h2hMatchup]);

  const columnsH2HStandings: ColumnDef<H2HStandingsData>[] = [
    {
      accessorKey: 'opponent_full_name',
      header: 'Opponent',
      cell: ({ row }) => <div className="px-2 py-1">{row.original.opponent_name}</div>,
    },
    {
      accessorKey: 'games_played',
      header: () => <div className="w-full text-center">GP</div>,
      cell: ({ row }) => <div className="text-center">{row.original.matchups}</div>,
      minSize: 90,
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

  const activeError = (ownersQueryError || standingsQueryError || matchupsQueryError || h2hMatchupQueryError);

  if (loadingOwners) return <StandingsTableSkeleton/>;
  
  if (activeError) return (
    <div className="p-8 text-center text-red-500">
      <h2>Error loading league data</h2>
      <p>{activeError instanceof Error ? activeError.message : activeError}</p>
    </div>
  )

  return (
    <div className="space-y-4 my-4 px-2">
      <CustomSelect
        title="Owner"
        placeholder="Choose an owner"
        items={members}
        onValueChange={(val) => setSelectedOwnerName(val)}
      />
      <DataTable
        columns={columnsH2HStandings}
        data={standings || []}
        initialSorting={[{ id: 'win_pct', desc: true }]}
        selectedRow={standings?.find(team => team.opponent_name === selectedOpponentName) ?? null}
        onRowClick={(row) => setSelectedOpponentName(row.opponent_name)}
      />
      <MatchupSheet
        matchup={activeMatchup!}
        open={expandedBoxScoreOpen && !!activeMatchup}
        onClose={() => {
          setSelectedWeek(null);
          setExpandedBoxScoreOpen(false);
        }}
      />
      {selectedOwnerName && selectedOpponentName ? (
        <>
        <h2 className="font-bold text-center">
          All Time Matchup Results: {selectedOwnerName} vs. {selectedOpponentName}
        </h2>
        <DataTable
          columns={columnsH2HMatchups(setSelectedSeason, setSelectedWeek)}
          data={scoresProcessed || []}
          initialSorting={[
            { id: 'season', desc: false },
            { id: 'week', desc: false },
          ]}
          selectedRow={
          selectedSeason && selectedWeek
            ? matchups!.find((matchup) => matchup.season === selectedSeason && matchup.week === selectedWeek) ?? null
            : null
          }
          onRowClick={(row) => {
            setSelectedSeason(row.season);
            setSelectedWeek(row.week);
          }}
        />
        </>
      ): (
        <></>
      )}
    </div>
  )
};

export default H2HStandings;