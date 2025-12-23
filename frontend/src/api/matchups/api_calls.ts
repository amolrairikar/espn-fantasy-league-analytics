import apiClient from "@/api/api_client";
import type { GetMatchups } from "@/api/matchups/types"

// Fetch matchups
export async function fetchMatchups(
  league_id: string,
  platform: string,
  playoff_filter: string,
  team1_id?: string,
  team2_id?: string,
  week_number?: string,
  season?: string,
): Promise<GetMatchups> {
  const response = await apiClient.get<GetMatchups>(`matchups`, {
    params: {
      league_id,
      platform,
      playoff_filter,
      team1_id,
      team2_id,
      week_number,
      season,
    },
  });
  return response.data;
}