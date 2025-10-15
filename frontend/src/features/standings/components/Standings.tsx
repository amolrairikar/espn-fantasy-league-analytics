import { useEffect, useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import AllTimeStandings from '@/features/standings/components/AllTimeStandings';
import SeasonStandings from '@/features/standings/components/SeasonStandings';
import H2HStandings from '@/features/standings/components/H2HStandings';

function Standings() {
  const [activeStandingsTab, setActiveStandingsTab] = useState<string>(() => {
    return localStorage.getItem('standingsTab') || 'all-time';
  });

  // update localStorage whenever tab changes
  useEffect(() => {
    localStorage.setItem('standingsTab', activeStandingsTab);
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
          <AllTimeStandings />
        </TabsContent>
        <TabsContent value="season">
          <SeasonStandings />
        </TabsContent>
        <TabsContent value="h2h">
          <H2HStandings />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default Standings;
