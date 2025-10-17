import { useMutation } from '@tanstack/react-query';
import type { UseMutationOptions } from '@tanstack/react-query';
import { request } from '@/components/utils/api_fetch';
import type { APIResponse } from '@/components/types/api_response_types';

export function usePostResource<Payload, ResponseData>(
  path: string,
  mutationOptions?: Omit<UseMutationOptions<APIResponse<ResponseData>, Error, Payload>, 'mutationFn'>,
) {
  return useMutation<APIResponse<ResponseData>, Error, Payload>({
    mutationFn: async (payload: Payload) => {
      return await request<ResponseData>(path, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },
    ...mutationOptions,
  });
}
