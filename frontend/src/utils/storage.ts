/**
 * utils/storage.ts
 * localStorage 封装，支持过期时间、自动 JSON 序列化
 */

interface StorageItem<T = any> {
  value: T;
  expire?: number; // 过期时间戳（毫秒）
}

export const storage = {
  /**
   * 设置存储
   * @param key 键
   * @param value 值（自动 JSON 序列化）
   * @param expireMs 过期毫秒数（可选）
   */
  set<T = any>(key: string, value: T, expireMs?: number): void {
    const item: StorageItem<T> = { value };
    if (expireMs) {
      item.expire = Date.now() + expireMs;
    }
    try {
      localStorage.setItem(key, JSON.stringify(item));
    } catch (e) {
      console.warn('storage.set 失败：', e);
    }
  },

  /**
   * 读取存储（自动检查过期）
   */
  get<T = any>(key: string): T | null {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return null;
      const item = JSON.parse(raw) as StorageItem<T>;
      if (item.expire && Date.now() > item.expire) {
        localStorage.removeItem(key);
        return null;
      }
      return item.value;
    } catch (e) {
      console.warn('storage.get 失败：', e);
      return null;
    }
  },

  remove(key: string): void {
    localStorage.removeItem(key);
  },

  clear(): void {
    localStorage.clear();
  },
};

/** sessionStorage 封装 */
export const session = {
  set<T = any>(key: string, value: T): void {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      console.warn('session.set 失败：', e);
    }
  },
  get<T = any>(key: string): T | null {
    try {
      const raw = sessionStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : null;
    } catch (e) {
      console.warn('session.get 失败：', e);
      return null;
    }
  },
  remove(key: string): void {
    sessionStorage.removeItem(key);
  },
  clear(): void {
    sessionStorage.clear();
  },
};

export default storage;
