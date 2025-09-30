export interface ApiResponse<T = unknown> {
  message: string;
  detail: string;
  data: T;
}
