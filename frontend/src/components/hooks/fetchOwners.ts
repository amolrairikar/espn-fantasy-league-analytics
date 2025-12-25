import { fetchLeagueOwners } from "@/api/owners/api_calls";
import { useQuery } from "@tanstack/react-query";

export function useFetchLeagueOwners(
  league_id: string,
  platform: string,
) {
  return useQuery({
    queryKey: ['owners', league_id, platform],
    queryFn: () => fetchLeagueOwners(
      league_id,
      platform,
    ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!league_id && !!platform, // only run if input args are available
  });
};
