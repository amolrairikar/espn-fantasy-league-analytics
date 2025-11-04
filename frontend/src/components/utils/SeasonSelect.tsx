import { useEffect, useState } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useGetResource } from '@/components/hooks/genericGetRequest';
import type { LeagueData } from '@/components/types/league_data';
import type { GetLeagueMetadata } from '@/features/login/types';

interface SeasonSelectProps {
  leagueData: LeagueData;
  onSeasonChange: (season: string) => void;
  selectedSeason?: string;
  defaultSeason?: string;
  className?: string;
}

export function SeasonSelect({
  leagueData,
  onSeasonChange,
  selectedSeason,
  defaultSeason,
  className,
}: SeasonSelectProps) {
  const [seasons, setSeasons] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const { refetch: refetchLeagueMetadata } = useGetResource<GetLeagueMetadata['data']>(
    `/leagues/${leagueData.leagueId}`,
    { platform: leagueData.platform },
  );

  useEffect(() => {
    const fetchSeasons = async () => {
      try {
        setLoading(true);
        const response = await refetchLeagueMetadata();
        const fetchedSeasons = response.data?.data?.seasons ?? [];
        setSeasons(fetchedSeasons);

        if (fetchedSeasons.length > 0) {
          const latestSeason = fetchedSeasons.sort((a, b) => Number(b) - Number(a))[0];

          // ✅ only set a default if parent hasn't already set one
          if (!selectedSeason) {
            const initialSeason = defaultSeason ?? latestSeason;
            onSeasonChange(initialSeason);
          }
        }
      } catch (err) {
        console.error('Error fetching seasons:', err);
      } finally {
        setLoading(false);
      }
    };

    void fetchSeasons();
  }, [refetchLeagueMetadata, defaultSeason, onSeasonChange, selectedSeason]);

  const handleSeasonChange = (value: string) => {
    onSeasonChange(value);
  };

  return (
    <div className={`flex items-center space-x-4 ${className ?? ''}`}>
      <label htmlFor="season" className="font-medium text-sm w-20 md:w-auto">
        Season:
      </label>
      <Select onValueChange={handleSeasonChange} value={selectedSeason ?? ''} disabled={loading}>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder={loading ? 'Loading seasons...' : 'Select a season'} />
        </SelectTrigger>
        <SelectContent>
          {loading ? (
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
