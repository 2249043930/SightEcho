/**
 * api/request.ts
 * axios 封装：拦截器、Token 注入、统一错误处理
 */
import axios, { AxiosError, type AxiosInstance, type AxiosResponse } from 'axios';
import { ElMessage } from 'element-plus';
import { useUserStore } from '@/stores/user';
import router from '@/router';

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const service: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const userStore = useUserStore();
    if (userStore.token) {
      config.headers = config.headers || {};
      (config.headers as any).Authorization = `Bearer ${userStore.token}`;
    }
    return config;
  },
  (err) => Promise.reject(err),
);

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const res = response.data;
    if (res.code === 0) {
      // **关键**：成功时只返回 data 部分，前端可直接用 resp.token 而不是 resp.data.token
      return res.data as any;
    }
    // 业务错误
    ElMessage({
      message: res.message || '请求失败',
      type: 'error',
      duration: 2500,
    });
    return Promise.reject(new Error(res.message || '请求失败'));
  },
  (err: AxiosError<ApiResponse>) => {
    const status = err.response?.status;
    const msg = err.response?.data?.message || err.message;
    if (status === 401) {
      const userStore = useUserStore();
      userStore.logout();
      ElMessage.warning('登录已过期，请重新登录');
      router.push({ name: 'Login' });
    } else if (status === 403) {
      ElMessage.error('无权限访问');
    } else if (status === 429) {
      ElMessage.warning('请求过于频繁，请稍后再试');
    } else if (status && status >= 500) {
      ElMessage.error('服务异常，请稍后重试');
    } else if (err.message.includes('Network')) {
      ElMessage.error('网络连接已断开');
    } else {
      ElMessage.error(msg || '请求失败');
    }
    return Promise.reject(err);
  },
);

export default service;
