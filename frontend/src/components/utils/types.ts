type ErrorResponseDetail = {
  status: string;
  detail: string;
  developer_detail: string;
};

type ErrorResponse = {
  detail: ErrorResponseDetail;
};

export type { ErrorResponse, ErrorResponseDetail };
