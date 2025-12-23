import apiClient from "@/api/api_client";
import type {
  GetChampionshipWinners,
  GetPlayerScores,
  GetTeamScores,
} from "@/api/records/types"

// Fetch championship winners
export async function getChampionshipWinner(
  leagueId: string, platform: string, recordType: string
): Promise<GetChampionshipWinners> {
  const response = await apiClient.get<GetChampionshipWinners>(`alltime_records`, {
    params: { league_id: leagueId, platform: platform, record_type: recordType },
  });
  return response.data;
}

// Fetch player scoring records
export async function getPlayerRecords(
  leagueId: string, platform: string, recordType: string
): Promise<GetPlayerScores> {
  const response = await apiClient.get<GetPlayerScores>(`alltime_records`, {
    params: { league_id: leagueId, platform: platform, record_type: recordType },
  });
  return response.data;
}

// Fetch team scoring records
export async function getTeamRecords(
  leagueId: string, platform: string, recordType: string
): Promise<GetTeamScores> {
  const response = await apiClient.get<GetTeamScores>(`alltime_records`, {
    params: { league_id: leagueId, platform: platform, record_type: recordType },
  });
  return response.data;
}
