import { useEffect, useRef, useState, type RefObject } from 'react';
import type { GridApi } from 'ag-grid-community';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import AllTimeStandings from '@/features/standings/components/AllTimeStandings';
import SeasonStandings from '@/features/standings/components/SeasonStandings';
import H2HStandings from '@/features/standings/components/H2HStandings';

function Standings() {
  const [activeStandingsTab, setActiveStandingsTab] = useState<string>(() => {
    return localStorage.getItem('standingsTab') || 'all-time';
  });

  const allTimeGridApiRef = useRef<GridApi | null>(null);
  const seasonGridApiRef = useRef<GridApi | null>(null);
  const h2hGridApiRef = useRef<GridApi | null>(null);

  const autoSizeNonPinnedColumns = (gridApi: RefObject<GridApi>) => {
    if (!gridApi?.current) return;

    const allColumns = gridApi.current.getColumns() ?? [];
    const nonPinnedColumns = allColumns.filter((col) => col.getPinned() !== 'left');
    const columnIds = nonPinnedColumns.map((col) => col.getId());

    if (columnIds.length) {
      gridApi.current.autoSizeColumns(columnIds, false);
    }
  };

  // update localStorage whenever tab changes
  useEffect(() => {
    localStorage.setItem('standingsTab', activeStandingsTab);
  }, [activeStandingsTab]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (activeStandingsTab === 'all-time') {
        autoSizeNonPinnedColumns(allTimeGridApiRef as RefObject<GridApi>);
      } else if (activeStandingsTab === 'season') {
        autoSizeNonPinnedColumns(seasonGridApiRef as RefObject<GridApi>);
      } else if (activeStandingsTab === 'h2h') {
        autoSizeNonPinnedColumns(h2hGridApiRef as RefObject<GridApi>);
      }
    }, 50); // small delay to ensure tab content is visible

    return () => clearTimeout(timeout);
  }, [activeStandingsTab]);

  return (
    <div>
      <Tabs value={activeStandingsTab} onValueChange={(val) => setActiveStandingsTab(val)} className="w-full">
        <div className="flex justify-center">
          <TabsList className="grid grid-cols-3">
            <TabsTrigger value="all-time" className="text-center">
              All-Time
            </TabsTrigger>
            <TabsTrigger value="season" className="text-center">
              Season
            </TabsTrigger>
            <TabsTrigger value="h2h" className="text-center">
              H2H
            </TabsTrigger>
          </TabsList>
        </div>
        <TabsContent value="all-time">
          <AllTimeStandings gridApiRef={allTimeGridApiRef} />
        </TabsContent>
        <TabsContent value="season">
          <SeasonStandings gridApiRef={seasonGridApiRef} />
        </TabsContent>
        <TabsContent value="h2h">
          <H2HStandings gridApiRef={h2hGridApiRef} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default Standings;
