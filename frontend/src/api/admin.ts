/**
 * api/admin.ts
 * 管理端：统计、Prompt、监控、反馈
 */
import request from './request';

export interface AdminStatsResp {
  totalUsers: number;
  todayActive: number;
  todayCalls: number;
  successRate: number;
  trend: { date: string; calls: number }[];
  distribution: { type: string; value: number }[];
}

export function getAdminStats() {
  return request.get<any, AdminStatsResp>('/admin/stats');
}

export interface PromptItem {
  id: string;
  type: string;
  name: string;
  content: string;
  version: number;
  enabled: boolean;
  updatedAt: string;
}
export function listPrompts() {
  return request.get<any, PromptItem[]>('/admin/prompts');
}
export function createPrompt(payload: Partial<PromptItem>) {
  return request.post<any, PromptItem>('/admin/prompts', payload);
}
export function updatePrompt(id: string, payload: Partial<PromptItem>) {
  return request.put<any, PromptItem>(`/admin/prompts/${id}`, payload);
}
export function deletePrompt(id: string) {
  return request.delete(`/admin/prompts/${id}`);
}

export interface MonitorResp {
  qps: number;
  successRate: number;
  avgLatency: number;
  endpoints: { path: string; qps: number; success: number; fail: number }[];
}
export function getMonitor() {
  return request.get<any, MonitorResp>('/admin/monitor');
}

export interface FeedbackItem {
  id: string;
  userId: string;
  recognitionId: string;
  rating: number;
  comment?: string;
  status: 'pending' | 'resolved';
  createdAt: string;
}
export function listFeedback(params: { status?: 'pending' | 'resolved'; page?: number; pageSize?: number }) {
  return request.get<any, { list: FeedbackItem[]; total: number }>('/admin/feedback', { params });
}
export function resolveFeedback(id: string) {
  return request.put(`/admin/feedback/${id}/resolve`);
}
