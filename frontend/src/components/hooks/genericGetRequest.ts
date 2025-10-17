import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import { request } from '@/components/utils/api_fetch';
import type { APIResponse } from '@/components/types/api_response_types';

export async function getResource<T>(
  basePath: string,
  queryParams: Record<string, string | number | boolean | undefined> = {},
): Promise<APIResponse<T>> {
  const search = new URLSearchParams(
    Object.entries(queryParams)
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)]),
  );

  const apiPath = `${basePath}${search.size ? `?${search}` : ''}`;
  const res = await request<T>(apiPath);
  return res;
}

export function useGetResource<T>(
  basePath: string,
  queryParams: Record<string, string | number | boolean | undefined> = {},
  queryOptions?: Omit<UseQueryOptions<APIResponse<T>>, 'queryKey' | 'queryFn'>,
) {
  const search = new URLSearchParams(
    Object.entries(queryParams)
      .filter(([, v]) => v !== undefined) // drop undefineds
      .map(([k, v]) => [k, String(v)]), // stringify numbers
  );

  const apiPath = `${basePath}${search.size ? `?${search}` : ''}`;

  return useQuery<APIResponse<T>>({
    queryKey: ['get', basePath, queryParams],
    queryFn: async () => {
      const res = await request<T>(apiPath);
      return res;
    },
    ...queryOptions,
  });
}
