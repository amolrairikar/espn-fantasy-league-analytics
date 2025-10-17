import { BASE_URL } from '@/components/utils/constants';
import type { APIResponse, ErrorResponse } from '@/components/types/api_response_types';

// Generic fetch wrapper
export async function request<T>(endpoint: string, options?: RequestInit): Promise<APIResponse<T>> {
  const full_api_url: string = `${BASE_URL}${endpoint}`;
  console.log('Making request to URL: ', full_api_url);
  const res = await fetch(full_api_url, {
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': import.meta.env.VITE_API_KEY,
      ...options?.headers,
    },
    ...options,
  });

  // Handle HTTP errors
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const err = (await res.json()) as unknown as ErrorResponse;
      if (typeof err.detail === 'string') message = err.detail;
    } catch {
      console.error('Failed to parse error JSON');
    }

    const error = new Error(message) as Error & { status?: number };
    error.status = res.status;
    throw error;
  }

  // Parse JSON for successful response
  const data = (await res.json()) as unknown as APIResponse<T>;
  return data;
}
