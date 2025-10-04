import { useMutation } from '@tanstack/react-query';
import type { UseMutationOptions } from '@tanstack/react-query';
import { request } from '@/components/utils/api_fetch';

export async function putResource<Payload, ResponseData>(
  path: string,
  payload: Payload,
  queryParams: Record<string, string | number | undefined> = {},
): Promise<ResponseData> {
  const search = new URLSearchParams(
    Object.entries(queryParams)
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)]),
  );

  const apiPath = `${path}${search.size ? `?${search}` : ''}`;

  return request<ResponseData>(apiPath, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function usePutResource<Payload, ResponseData>(
  path: string,
  mutationOptions?: Omit<UseMutationOptions<ResponseData, Error, Payload>, 'mutationFn'>,
) {
  return useMutation<ResponseData, Error, Payload>({
    mutationFn: (payload: Payload) =>
      request<ResponseData>(path, {
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
    ...mutationOptions,
  });
}
