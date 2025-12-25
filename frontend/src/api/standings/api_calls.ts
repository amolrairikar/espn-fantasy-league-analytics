import apiClient from "@/api/api_client";
import type {
  GetAllTimeStandings,
  GetH2HStandings,
  GetPlayoffStandings,
  GetSeasonStandings,
  GetWeeklyStandings,
} from "@/api/standings/types"

// Fetch all-time standings
export async function fetchAllTimeStandings(
  leagueId: string, platform: string, standingsType: string
): Promise<GetAllTimeStandings> {
  const response = await apiClient.get<GetAllTimeStandings>(`standings`, {
    params: { league_id: leagueId, platform: platform, standings_type: standingsType },
  });
  return response.data;
}

// Fetch season standings for all teams in one season
export async function fetchSingleSeasonStandings(
  leagueId: string, platform: string, standingsType: string, season: string
): Promise<GetSeasonStandings> {
  const response = await apiClient.get<GetSeasonStandings>(`standings`, {
    params: { league_id: leagueId, platform: platform, standings_type: standingsType, season: season },
  });
  return response.data;
}

// Fetch season standings for one team over all seasons
export async function fetchMultipleSeasonStandings(
  leagueId: string, platform: string, standingsType: string, team: string
): Promise<GetSeasonStandings> {
  const response = await apiClient.get<GetSeasonStandings>(`standings`, {
    params: { league_id: leagueId, platform: platform, standings_type: standingsType, team: team },
  });
  return response.data;
}

// Fetch H2H standings
export async function fetchH2HStandings(
  leagueId: string, platform: string, standingsType: string
): Promise<GetH2HStandings> {
  const response = await apiClient.get<GetH2HStandings>(`standings`, {
    params: { league_id: leagueId, platform: platform, standings_type: standingsType },
  });
  return response.data;
}

// Fetch weekly standings
export async function fetchWeeklyStandings(
  leagueId: string, platform: string, standingsType: string
): Promise<GetWeeklyStandings> {
  const response = await apiClient.get<GetWeeklyStandings>(`standings`, {
    params: { league_id: leagueId, platform: platform, standings_type: standingsType },
  });
  return response.data;
}

// Fetch playoff standings
export async function fetchPlayoffStandings(
  leagueId: string, platform: string, standingsType: string
): Promise<GetPlayoffStandings> {
  const response = await apiClient.get<GetPlayoffStandings>(`standings`, {
    params: { league_id: leagueId, platform: platform, standings_type: standingsType },
  });
  return response.data;
}
