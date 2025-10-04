import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { request } from '@/components/utils/api_fetch';

export async function getResource<T>(
  basePath: string,
  queryParams: Record<string, string | number | undefined> = {},
): Promise<T> {
  const search = new URLSearchParams(
    Object.entries(queryParams)
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)]),
  );

  const apiPath = `${basePath}${search.size ? `?${search}` : ''}`;
  return request<T>(apiPath);
}

export function useGetResource<T>(
  basePath: string,
  queryParams: Record<string, string | number | undefined> = {},
  queryOptions?: Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>,
) {
  const search = new URLSearchParams(
    Object.entries(queryParams)
      .filter(([, v]) => v !== undefined) // drop undefineds
      .map(([k, v]) => [k, String(v)]), // stringify numbers
  );

  const apiPath = `${basePath}${search.size ? `?${search}` : ''}`;

  return useQuery<T>({
    queryKey: ['get', basePath, queryParams],
    queryFn: () => request<T>(apiPath),
    ...queryOptions,
  });
}
