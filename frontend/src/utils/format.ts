/**
 * utils/format.ts
 * 文本、时间、数字格式化工具
 */
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

/** 时间戳格式化为 YYYY-MM-DD HH:mm:ss */
export function formatDateTime(timestamp: number | string | Date, fmt = 'YYYY-MM-DD HH:mm:ss'): string {
  return dayjs(timestamp).format(fmt);
}

/** 相对时间（如 3 分钟前） */
export function formatRelativeTime(timestamp: number | string | Date): string {
  return dayjs(timestamp).fromNow();
}

/** 仅显示日期 */
export function formatDate(timestamp: number | string | Date): string {
  return dayjs(timestamp).format('YYYY-MM-DD');
}

/** 文件大小（B / KB / MB） */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

/** 数字千分位 */
export function formatNumber(num: number): string {
  return num.toLocaleString('zh-CN');
}

/** 百分比 */
export function formatPercent(value: number, total: number, fixed = 1): string {
  if (total === 0) return '0%';
  return `${((value / total) * 100).toFixed(fixed)}%`;
}

/** 截断文本 */
export function truncate(text: string, max = 50): string {
  if (!text) return '';
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

/** 脱敏手机号 / 邮箱 */
export function maskEmail(email: string): string {
  if (!email || !email.includes('@')) return email;
  const [name, domain] = email.split('@');
  const visible = name.length <= 2 ? name[0] : `${name[0]}***${name[name.length - 1]}`;
  return `${visible}@${domain}`;
}

export { dayjs };
