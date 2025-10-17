import { useMutation } from '@tanstack/react-query';
import type { UseMutationOptions } from '@tanstack/react-query';
import { request } from '@/components/utils/api_fetch';
import type { APIResponse } from '@/components/types/api_response_types';

export async function putResource<Payload, ResponseData>(
  path: string,
  payload: Payload,
  queryParams: Record<string, string | number | undefined> = {},
): Promise<APIResponse<ResponseData>> {
  const search = new URLSearchParams(
    Object.entries(queryParams)
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)]),
  );

  const apiPath = `${path}${search.size ? `?${search}` : ''}`;
  const res = await request<ResponseData>(apiPath, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  return res;
}

export function usePutResource<Payload, ResponseData>(
  path: string,
  mutationOptions?: Omit<UseMutationOptions<APIResponse<ResponseData>, Error, Payload>, 'mutationFn'>,
) {
  return useMutation<APIResponse<ResponseData>, Error, Payload>({
    mutationFn: async (payload: Payload) => {
      const res = await request<ResponseData>(path, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
      return res;
    },
    ...mutationOptions,
  });
}
