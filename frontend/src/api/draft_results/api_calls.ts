import apiClient from "@/api/api_client";
import type { GetDraftResults } from "@/api/draft_results/types"

// Fetch draft results
export async function fetchDraftResults(
  leagueId: string, platform: string, season: string
): Promise<GetDraftResults> {
  const response = await apiClient.get<GetDraftResults>(`draft-results`, {
    params: { league_id: leagueId, platform: platform, season: season },
  });
  return response.data;
};
