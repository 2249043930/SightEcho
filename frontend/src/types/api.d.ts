/**
 * types/api.d.ts
 * 通用 API 类型声明
 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

export interface PageResp<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface IdResp {
  id: string;
}
