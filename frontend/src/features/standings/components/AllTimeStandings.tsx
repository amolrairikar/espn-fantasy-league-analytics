import { useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { useDatabase } from '@/components/utils/DatabaseContext';
import { useDuckDbQuery } from '@/components/hooks/useDuckDbQuery';
import { DataTable } from '@/components/utils/dataTable';
import type { AllTimeStandingsData } from '@/features/standings/types';
import { StandingsTableSkeleton } from '@/features/standings/components/SkeletonStandingsTable';

function AllTimeStandings() {
  const { db } = useDatabase();
  const [selectedOwnerName, setSelectedOwnerName] = useState<string | null>(null);

  const { data: standings, error: standingsQueryError, loading: loadingStandings } = useDuckDbQuery<any>(
    db,
    `
    SELECT * FROM league_all_time_standings ORDER BY wins DESC;
    `
  );

  const selectedOwnerId = standings?.find(s => s.owner_name === selectedOwnerName)?.owner_id;

  const { data: ownerStandings, error: ownerStandingsQueryError, loading: loadingOwnerStandings } = useDuckDbQuery<any>(
    db,
    `
    SELECT * FROM league_regular_season_standings WHERE owner_id = '${selectedOwnerId}' ORDER BY season ASC;
    `
  );

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

  const chartConfig = {
    desktop: {
      label: 'Wins',
      color: 'var(--chart-1)',
    },
  } satisfies ChartConfig;

  const isLoading = (loadingStandings || loadingOwnerStandings);
  const activeError = (standingsQueryError || ownerStandingsQueryError);

  if (isLoading) return <StandingsTableSkeleton/>;
  
  if (activeError) return (
    <div className="p-8 text-center text-red-500">
      <h2>Error loading league data</h2>
      <p>{activeError instanceof Error ? activeError.message : activeError}</p>
    </div>
  )

  return(
    <div className="space-y-4 my-4 px-2">
      {selectedOwnerName ? (
        <>
          <DataTable
            columns={columns}
            data={standings || []}
            initialSorting={[{ id: 'win_pct', desc: true }]}
            selectedRow={standings!.find(team => team.owner_name === selectedOwnerName) ?? null}
            onRowClick={(row) => setSelectedOwnerName(row.owner_name)}
          />
          <h1 className="font-semibold text-center">Wins Per Season for {selectedOwnerName}</h1>
          <ChartContainer config={chartConfig} className="h-50 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart accessibilityLayer data={ownerStandings!}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="season" tickLine={false} tickMargin={10} axisLine={false} />
              <YAxis dataKey="wins" domain={[0, 12]} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="wins" fill="var(--color-desktop)" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </>
      ) : (
        <div className="space-y-4 my-4 px-2">
          <p className="text-sm text-muted-foreground italic">
            Click on an owner's name to display a chart of their wins per season
          </p>
          <DataTable
            columns={columns}
            data={standings || []}
            initialSorting={[{ id: 'win_pct', desc: true }]}
            selectedRow={standings!.find(team => team.owner_name === selectedOwnerName) ?? null}
            onRowClick={(row) => setSelectedOwnerName(row.owner_name)}
          /> 
        </div>
      )}
    </div>
  )
}

export default AllTimeStandings;