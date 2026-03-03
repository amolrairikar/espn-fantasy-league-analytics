import apiClient from "@/api/api_client";
import type { ValidateLeagueReponse } from "@/api/league_metadata/types";

// Validate league metadata
export async function validateLeagueMetadata(
  leagueId: string,
  platform: string,
  season: string,
  espn_s2_cookie: string,
  swid_cookie: string
): Promise<ValidateLeagueReponse> {
  const response = await apiClient.get<ValidateLeagueReponse>('/validate-league', {
    params: {
      league_id: leagueId,
      platform: platform,
      season: season,
      espn_s2_cookie: espn_s2_cookie,
      swid_cookie: swid_cookie,
    },
  });
  return response.data;
}
