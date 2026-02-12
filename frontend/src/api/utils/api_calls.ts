import apiClient from "@/api/api_client";
import type { GetDeleteStatus } from "@/api/utils/types"

// Fetch draft results
export async function fetchDeleteStatus(
  leagueId: string
): Promise<GetDeleteStatus> {
  const response = await apiClient.delete<GetDeleteStatus>(`delete_league`, {
    params: { league_id: leagueId },
  });
  return response.data;
};
