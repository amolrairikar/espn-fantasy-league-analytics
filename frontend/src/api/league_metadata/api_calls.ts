import apiClient from "@/api/api_client";
import type { 
  GetLeagueMetadata,
  ValidateLeagueReponse,
  PostLeagueMetadataPayload,
  PostLeagueMetadataResponse,
} from "@/api/league_metadata/types";

// Fetch league metadata
export async function getLeagueMetadata(leagueId: string, platform: string): Promise<GetLeagueMetadata> {
  const response = await apiClient.get<GetLeagueMetadata>(`/leagues/${leagueId}`, {
    params: { platform: platform },
  });
  return response.data;
}

// Validate league metadata
export async function validateLeagueMetadata(
  leagueId: string,
  platform: string,
  privacy: string,
  season: string,
  espn_s2_cookie: string,
  swid_cookie: string
): Promise<ValidateLeagueReponse> {
  const response = await apiClient.get<ValidateLeagueReponse>('/leagues/validate', {
    params: {
      league_id: leagueId,
      platform: platform,
      privacy: privacy,
      season: season,
      espn_s2_cookie: espn_s2_cookie,
      swid_cookie: swid_cookie,
    },
  });
  return response.data;
}

// Create league metadata entry
export async function postLeagueMetadata(payload: PostLeagueMetadataPayload): Promise<PostLeagueMetadataResponse> {
  const response = await apiClient.post('/leagues', payload);
  return response.data;
}

// Update league metadata entry
export async function putLeagueMetadata(payload: PostLeagueMetadataPayload): Promise<PostLeagueMetadataResponse> {
  const response = await apiClient.put<PostLeagueMetadataResponse>(`/leagues/${payload.league_id}`, payload);
  return response.data;
}
