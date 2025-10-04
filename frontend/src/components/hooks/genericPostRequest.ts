import { useMutation } from '@tanstack/react-query';
import type { UseMutationOptions } from '@tanstack/react-query';
import { request } from '@/components/utils/api_fetch';

export function usePostResource<Payload, ResponseData>(
  path: string,
  mutationOptions?: Omit<UseMutationOptions<ResponseData, Error, Payload>, 'mutationFn'>,
) {
  return useMutation<ResponseData, Error, Payload>({
    mutationFn: (payload: Payload) =>
      request<ResponseData>(path, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    ...mutationOptions,
  });
}
