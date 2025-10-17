type ErrorResponse = {
  detail: string;
};

type APIResponse<T = unknown> = {
  detail: string;
  data?: T;
};

export type { APIResponse, ErrorResponse };
