import { BASE_URL } from '@/components/utils/constants';
import type { ErrorResponse, ErrorResponseDetail } from '@/components/utils/types';

// Generic fetch wrapper
export async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
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
    let message: string = String(res.status);
    console.log(`Error code: ${message}`);

    try {
      const data: unknown = await res.json();
      if (data && typeof data === 'object' && data != null && 'detail' in data) {
        const detailObj = (data as ErrorResponse).detail;
        const keys: (keyof ErrorResponseDetail)[] = ['status', 'detail', 'developer_detail'];
        if (keys.every((key) => key in detailObj && typeof detailObj[key] === 'string')) {
          message = detailObj.detail;
          console.log('Error detail:', message);
        }
      }
    } catch (err) {
      // JSON parse failed, keep default message
      console.error('Failed to parse error response JSON:', err);
      const text = await res.text();
      console.error('Error response text:', text);
    }

    // Throw an error with the status code attached
    const errorWithStatus = new Error(message) as Error & { status?: number };
    errorWithStatus.status = res.status;
    throw errorWithStatus;
  }

  // Parse JSON for successful response
  const data: unknown = await res.json();
  return data as T;
}
