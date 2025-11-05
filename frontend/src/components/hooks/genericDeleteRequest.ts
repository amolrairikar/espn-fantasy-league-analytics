import { useMutation, type UseMutationOptions } from '@tanstack/react-query';
import { request } from '@/components/utils/api_fetch';
import type { APIResponse } from '@/components/types/api_response_types';

export async function deleteResource<T>(
  basePath: string,
  queryParams: Record<string, string | number | boolean | undefined> = {},
): Promise<APIResponse<T>> {
  const search = new URLSearchParams(
    Object.entries(queryParams)
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)]),
  );

  const apiPath = `${basePath}${search.size ? `?${search}` : ''}`;
  const res = await request<T>(apiPath, { method: 'DELETE' });
  return res;
}

export function useDeleteResource<T>(
  basePath: string,
  mutationOptions?: UseMutationOptions<APIResponse<T>, unknown, Record<string, string | number | boolean | undefined>>,
) {
  return useMutation<APIResponse<T>, unknown, Record<string, string | number | boolean | undefined>>({
    mutationKey: ['delete', basePath],
    mutationFn: async (queryParams) => deleteResource<T>(basePath, queryParams),
    ...mutationOptions,
  });
}
