/**
 * api/auth.ts
 * 认证：邮箱验证码
 */
import request from './request';

export interface SendCodeParams {
  email: string;
}
export interface SendCodeResp {
  expire: number; // 验证码有效期（秒）
}
export interface LoginParams {
  email: string;
  code: string;
}
export interface LoginResp {
  token: string;
  expiresIn: number;
  refreshToken?: string;
}

export function sendEmailCode(params: SendCodeParams) {
  return request.post<any, SendCodeResp>('/auth/email-code', params);
}

export function loginByCode(params: LoginParams) {
  return request.post<any, LoginResp>('/auth/login', params);
}

export function logout() {
  return request.post('/auth/logout');
}
