import apiClient from "@/api/api_client";
import type { GetHealthCheck } from "@/api/health/types"

// Fetch API health status
export async function fetchHealthCheck(): Promise<GetHealthCheck> {
  const response = await apiClient.get<GetHealthCheck>(`health`, {
    params: {},
  });
  return response.data;
};
