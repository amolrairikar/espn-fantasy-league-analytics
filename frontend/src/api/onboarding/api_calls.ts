import apiClient from "@/api/api_client";
import type { 
  GetLeagueOnboardingStatus,
  PostLeagueOnboardingPayload,
  PostLeagueOnboardingResponse,
} from "@/api/onboarding/types";

// Fetch league onboarding status
export async function getLeagueOnboardingStatus(executionId: string): Promise<GetLeagueOnboardingStatus> {
  const response = await apiClient.get<GetLeagueOnboardingStatus>(`/onboard/${executionId}`);
  return response.data;
}

// Create a league onboarding entry
export async function postLeagueOnboarding(payload: PostLeagueOnboardingPayload): Promise<PostLeagueOnboardingResponse> {
  const response = await apiClient.post<PostLeagueOnboardingResponse>('/onboard', payload);
  return response.data;
}
