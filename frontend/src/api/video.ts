/**
 * api/video.ts
 * 视频流解析：提交任务、查询状态、SSE 实时获取结果
 */
import request from './request';

export type VideoScene = 'travel' | 'face' | 'ocr' | 'product' | 'currency';

export interface VideoParseResp {
  taskId: string;
  status: string;
}

export interface VideoFrame {
  idx: number;
  text: string;
  ts: number;
  frames_used?: number;
}

export interface VideoTaskStatus {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'not_found';
  frames?: VideoFrame[];
  started_at?: number;
  finished_at?: number;
  error?: string;
}

/** 提交视频流解析任务 */
export function startVideoParse(params: {
  src: string;
  scene?: VideoScene;
  fps?: number;
}) {
  return request.post<any, VideoParseResp>('/video/parse', null, {
    params,
  });
}

/** 查询任务状态（含已完成的 frames 列表） */
export function getVideoTask(taskId: string) {
  return request.get<any, VideoTaskStatus>(`/video/tasks/${taskId}`);
}

/** SSE 实时获取结果（用 EventSource 原生 API 走 baseURL 前缀） */
export function buildVideoStreamURL(taskId: string) {
  const base = (request.defaults.baseURL as string) || '';
  return `${base}/video/stream/${taskId}`;
}
