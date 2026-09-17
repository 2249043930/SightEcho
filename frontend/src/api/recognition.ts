/**
 * api/recognition.ts
 * 通用识别 + 历史记录 + 反馈
 */
import request from './request';

export type RecognitionType = 'travel' | 'ocr' | 'currency' | 'product' | 'face';

export interface RecognitionParams {
  type: RecognitionType;
  image?: Blob | File;
  extra?: Record<string, any>;
}

export interface RecognitionResult {
  id: string;
  type: RecognitionType;
  title: string;
  content: string;
  audioUrl?: string;
  thumbnail?: string;
  createdAt: string;
}

/**
 * WebRTC 实时帧识别结果（与 RecognitionResult 兼容，并携带额外字段）
 */
export interface LiveRecognitionResult extends RecognitionResult {
  priority?: 'high' | 'normal';
  framesUsed?: number;
  latencyMs?: number;
  resultJson?: {
    confidence?: number;
    is_demo?: boolean;
    is_fallback?: boolean;
    priority?: 'high' | 'normal';
    frames_used?: number;
    mode?: string;
  };
}

export interface HistoryParams {
  page?: number;
  pageSize?: number;
  type?: RecognitionType;
  keyword?: string;
}

export interface HistoryListResp {
  list: RecognitionResult[];
  total: number;
  page: number;
  pageSize: number;
}

export function recognize(params: RecognitionParams) {
  const form = new FormData();
  if (params.image) form.append('image', params.image);
  if (params.extra) form.append('extra', JSON.stringify(params.extra));
  return request.post<any, RecognitionResult>(`/recognition/${params.type}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

/**
 * WebRTC 实时帧识别
 *
 * 由前端 useLiveStream 收集到 N 张 base64 帧图后批量调用。
 *  - 1 ~ 8 张 base64 字符串，可含 "data:image/jpeg;base64," 前缀（后端会自动剥离）
 *  - 后端走 JoyAI-VL-Interaction 的视频流多帧推理
 *  - 返回中含 priority=high 表示命中危险关键词（视障场景里要立刻播报）
 */
export function recognizeLive(payload: {
  scene: RecognitionType;
  images: string[];
  extra?: Record<string, any>;
  saveRecord?: boolean;
}) {
  return request.post<any, LiveRecognitionResult>('/recognition/live', payload);
}

export function getHistory(params: HistoryParams) {
  return request.get<any, HistoryListResp>('/recognition/history', { params });
}

export function getHistoryDetail(id: string) {
  return request.get<any, RecognitionResult>(`/recognition/history/${id}`);
}

export function deleteHistory(id: string) {
  return request.delete(`/recognition/history/${id}`);
}

export function submitFeedback(payload: { id: string; rating: number; comment?: string }) {
  return request.post('/recognition/feedback', payload);
}
