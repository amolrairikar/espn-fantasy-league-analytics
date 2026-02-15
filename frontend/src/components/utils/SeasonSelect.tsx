import { useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { LeagueData } from '@/components/types/league_data';
import { getLeagueMetadata } from '@/api/league_metadata/api_calls';

interface SeasonSelectProps {
  leagueData: LeagueData;
  onSeasonChange: (season: string) => void;
  selectedSeason?: string;
  defaultSeason?: string;
  className?: string;
}

function useFetchLeagueMetadata(
  league_id: string,
  platform: string,
) {
  return useQuery({
    queryKey: ['league_metadata', league_id, platform],
    queryFn: () => getLeagueMetadata(
      league_id,
      platform,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform, // only run if input args are available
  });
};

export function SeasonSelect({
  leagueData,
  onSeasonChange,
  selectedSeason,
  defaultSeason,
  className,
}: SeasonSelectProps) {
  const { data: leagueMetadata, isLoading: loadingMetadata } = useFetchLeagueMetadata(
    leagueData!.leagueId,
    leagueData!.platform,
  );

  const seasons = useMemo(() => {
    const rawSeasons = leagueMetadata?.data?.seasons ?? [];
    // Sort descending (latest year first)
    return [...rawSeasons].sort((a, b) => Number(b) - Number(a));
  }, [leagueMetadata]);

  // useEffect just for the initial "Auto-Select" logic
  useEffect(() => {
    if (!loadingMetadata && seasons.length > 0 && !selectedSeason) {
      const initialSeason = defaultSeason ?? seasons[0];
      onSeasonChange(initialSeason);
    }
  }, [seasons, loadingMetadata, selectedSeason, defaultSeason, onSeasonChange]);

  const handleSeasonChange = (value: string) => {
    onSeasonChange(value);
  };

  return (
    <div className={`flex items-center space-x-4 ${className ?? ''}`}>
      <label htmlFor="season" className="font-medium text-sm w-20 md:w-auto">
        Season:
      </label>
      <Select onValueChange={handleSeasonChange} value={selectedSeason ?? ''} disabled={loadingMetadata}>
        <SelectTrigger className="w-50">
          <SelectValue placeholder={loadingMetadata ? 'Loading seasons...' : 'Select a season'} />
        </SelectTrigger>
        <SelectContent>
          {loadingMetadata ? (
            <SelectItem disabled value="loading">
              Loading...
            </SelectItem>
          ) : seasons.length > 0 ? (
            seasons.map((season) => (
              <SelectItem key={season} value={season}>
                {season}
              </SelectItem>
            ))
          ) : (
            <SelectItem disabled value="none">
              No seasons found
            </SelectItem>
          )}
        </SelectContent>
      </Select>
    </div>
  );
}
