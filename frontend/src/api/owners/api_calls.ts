import apiClient from "@/api/api_client";
import type {
  GetLeagueOwners
} from "@/api/owners/types"

// Fetch league owners
export async function fetchLeagueOwners(leagueId: string, platform: string): Promise<GetLeagueOwners> {
  const response = await apiClient.get<GetLeagueOwners>(`owners`, {
    params: { league_id: leagueId, platform: platform },
  });
  return response.data;
};
