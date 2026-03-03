import apiClient from "@/api/api_client";
import type {
  PostLeagueOnboardingPayload,
  PostLeagueOnboardingResponse,
} from "@/api/onboarding/types";

// Create a league onboarding entry
export async function postLeagueOnboarding(payload: PostLeagueOnboardingPayload): Promise<PostLeagueOnboardingResponse> {
  const response = await apiClient.post<PostLeagueOnboardingResponse>('/onboard', payload);
  return response.data;
}
