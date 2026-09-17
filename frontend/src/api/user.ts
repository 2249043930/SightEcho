/**
 * api/user.ts
 * 用户信息 + 设置
 */
import request from './request';
import type { UserProfile } from '@/stores/user';

export function getProfile() {
  return request.get<any, UserProfile>('/user/profile');
}

export function updateProfile(payload: Partial<UserProfile>) {
  return request.put<any, UserProfile>('/user/profile', payload);
}

export interface UserSettingsPayload {
  speed?: number;
  volume?: number;
  wakeEnabled?: boolean;
  autoAnnounce?: boolean;
  fontScale?: 'small' | 'medium' | 'large';
}
export function getUserSettings() {
  return request.get<any, UserSettingsPayload>('/user/settings');
}
export function updateUserSettings(payload: UserSettingsPayload) {
  return request.put<any, UserSettingsPayload>('/user/settings', payload);
}
