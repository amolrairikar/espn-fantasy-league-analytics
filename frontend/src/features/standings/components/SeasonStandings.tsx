import { useEffect, useMemo, useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import { useDatabase } from '@/components/utils/DatabaseContext';
import { useDuckDbQuery } from '@/components/hooks/useDuckDbQuery';
import { DataTable } from '@/components/utils/dataTable';
import { MatchupSheet } from '@/components/utils/MatchupSheet';
import { CustomSelect } from '@/components/utils/CustomSelectbox';
import type { MatchupTableView, RegularSeasonStandingsData } from '@/features/standings/types';
import type { Matchup } from '@/features/scores/types';
import { StandingsTableSkeleton } from '@/features/standings/components/SkeletonStandingsTable';

function SeasonStandings() {
  const { db } = useDatabase();
  const [selectedSeason, setSelectedSeason] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);
  const [expandedBoxScoreOpen, setExpandedBoxScoreOpen] = useState<boolean>(false);

  const { data: seasons, error: seasonsQueryError, loading: loadingSeasons } = useDuckDbQuery<any>(
    db,
    `
    SELECT DISTINCT season FROM league_members ORDER BY SEASON DESC;
    `
  );

  // Sync defaults when data first arrives
  useEffect(() => {
    if (seasons && !selectedSeason) {
      setSelectedSeason(defaultSeason);
    }
  }, [seasons]);

  const seasonOptions = seasons?.map(s => s.season) || [];
  const defaultSeason = seasonOptions.length > 0 ? seasonOptions.at(0) : "Loading...";

  const { data: standings, error: standingsQueryError, loading: loadingStandings } = useDuckDbQuery<any>(
    db,
    `
    SELECT
        s.*,
        p.status AS playoff_status,
        c.status AS championship_status,
    FROM league_regular_season_standings s
    LEFT JOIN league_postseason_teams p
        ON s.season = p.season
        AND s.owner_id = p.owner_id
        AND p.status IN ('MADE_PLAYOFFS', 'CLINCHED_FIRST_ROUND_BYE')
    LEFT JOIN league_postseason_teams c
        ON s.season = c.season
        AND s.owner_id = c.owner_id
        AND c.status = 'LEAGUE_CHAMPION'
    WHERE s.season = '${selectedSeason}'
    ORDER BY wins DESC;
    `
  );

  const selectedOwnerId = standings?.find(s => s.owner_name === selectedOwnerName)?.owner_id;
  const selectedTeamId = standings?.find(s => s.owner_name === selectedOwnerName)?.team_id;

  const { data: scores, error: scoresQueryError, loading: loadingScores } = useDuckDbQuery<any>(
    db,
    `
    SELECT *
    FROM league_matchups
    WHERE season = '${selectedSeason}'
    AND (home_team_full_name = '${selectedOwnerName}' OR away_team_full_name = '${selectedOwnerName}')
    AND playoff_tier_type = 'NONE';
    `
  );

  const scoresProcessed = useMemo(() => {
    if (!scores || !selectedTeamId) return [];
    return scores.map((matchup) => {
      // Determine if the selected owner is the Home or Away team
      const isHome = matchup.home_team_owner_id === selectedOwnerId;

      const ownerScore = isHome ? matchup.home_team_score : matchup.away_team_score;
      const opponentScore = isHome ? matchup.away_team_score : matchup.home_team_score;
      const opponentName = isHome ? matchup.away_team_full_name : matchup.home_team_full_name;

      // Logic for Outcome (Handles Wins, Losses, and Ties)
      let outcome = 'L';
      if (matchup.winner === selectedTeamId) {
        outcome = 'W';
      } else if (matchup.winner === null && matchup.home_team_score === matchup.away_team_score) {
        // Optional: Handle ties if your league allows them
        outcome = 'T';
      }

      return {
        ...matchup,
        season: matchup.season,
        week: Number(matchup.week),
        opponent_full_name: opponentName,
        result: `${ownerScore} - ${opponentScore}`,
        outcome: outcome,
      };
    });
  }, [scores, selectedOwnerId, selectedTeamId]);

  const { data: matchup, error: matchupQueryError } = useDuckDbQuery<Matchup>(
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

  const columnsStandings: ColumnDef<RegularSeasonStandingsData>[] = [
    {
      accessorKey: 'owner_full_name',
      header: 'Owner',
      cell: ({ row }) => {
        const isSelected = row.original.owner_name === selectedOwnerName;
        const { playoff_status, championship_status } = row.original;
        const crown = championship_status === 'LEAGUE_CHAMPION' ? ' 👑' : '';

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
            onClick={() => setSelectedOwnerName(row.original.owner_name)}
          >
            {row.original.owner_name}
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
      header: () => <div className="w-full text-center">Win %</div>,
      cell: ({ row }) => <div className="text-center">{row.original.win_pct.toFixed(3)}</div>,
      minSize: 100,
    },
    {
      accessorKey: 'points_for',
      header: () => <div className="w-full text-center">Points For</div>,
      cell: ({ row }) => <div className="text-center">{row.original.total_pf.toFixed(2)}</div>,
      minSize: 130,
    },
    {
      accessorKey: 'points_against',
      header: () => <div className="w-full text-center">Points Against</div>,
      cell: ({ row }) => <div className="text-center">{row.original.total_pa.toFixed(2)}</div>,
      minSize: 130,
    },
    {
      accessorKey: 'points_differential',
      header: () => <div className="w-full text-center">Differential</div>,
      cell: ({ row }) => {
        const value = row.original.total_pf - row.original.total_pa;

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
      cell: ({ row }) => <div className="text-center">
        {`${row.original.total_vs_league_wins} - ${row.original.total_vs_league_losses}`}
      </div>,
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

  const isLoading = (loadingSeasons || loadingStandings || loadingScores);
  const activeError = (seasonsQueryError || standingsQueryError || scoresQueryError || matchupQueryError);

  if (isLoading) return <StandingsTableSkeleton/>;
  
  if (activeError) return (
    <div className="p-8 text-center text-red-500">
      <h2>Error loading league data</h2>
      <p>{activeError instanceof Error ? activeError.message : activeError}</p>
    </div>
  )

  return (
    <div className="space-y-4 my-4 px-2">
      <CustomSelect
        title="Season"
        placeholder={selectedSeason || defaultSeason!}
        items={seasonOptions}
        onValueChange={(val) => setSelectedSeason(val)}
      />
      {selectedOwnerName ? (
        <>
        <DataTable
          columns={columnsStandings}
          data={standings || []}
          initialSorting={[{ id: 'win_pct', desc: true }]}
          selectedRow={standings!.find(team => team.owner_name === selectedOwnerName) ?? null}
          onRowClick={(row) => setSelectedOwnerName(row.owner_name)}
        />
        <p className="text-sm text-muted-foreground italic mt-1">
          z = first round bye | x = playoffs | 👑 = won the championship
          <br />
          Note that playoff qualification status cannot be determined until the end of the season due to ESPN API limitations.
        </p>
        <h1 className="font-semibold mt-6 text-center">Season Schedule for {selectedOwnerName}</h1>
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
        <>
        <DataTable
          columns={columnsStandings}
          data={standings || []}
          initialSorting={[{ id: 'win_pct', desc: true }]}
          selectedRow={standings!.find(team => team.owner_name === selectedOwnerName) ?? null}
          onRowClick={(row) => setSelectedOwnerName(row.owner_name)}
        />
        <p className="text-sm text-muted-foreground italic mt-1">
          z = first round bye | x = playoffs | 👑 = won the championship
          <br />
          Note that playoff qualification status cannot be determined until the end of the season due to ESPN API limitations.
        </p>
        </>
      )}
      <MatchupSheet
        matchup={activeMatchup!}
        open={expandedBoxScoreOpen && !!activeMatchup}
        onClose={() => {
          setSelectedWeek(null);
          setExpandedBoxScoreOpen(false);
      }}
      />
    </div>
  );
};

export default SeasonStandings