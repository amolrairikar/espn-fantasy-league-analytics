import apiClient from "@/api/api_client";
import type {
  GetLeagueDatabaseResponse
} from "@/api/database/types";

// Get league database
export async function getLeagueDatabase(league_id: string): Promise<GetLeagueDatabaseResponse> {
  const response = await apiClient.get<GetLeagueDatabaseResponse>('/database', {
    params: {
      league_id: league_id,
    }
  });
  return response.data;
}
