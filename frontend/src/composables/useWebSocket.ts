/**
 * composables/useWebSocket.ts
 * 通用 WebSocket 封装：自动重连、心跳、消息分发
 */
import { ref, onBeforeUnmount } from 'vue';

export interface UseWebSocketOptions {
  url: string;
  protocols?: string | string[];
  heartbeatInterval?: number;
  heartbeatMessage?: string;
  reconnect?: boolean;
  reconnectDelay?: number;
  maxReconnectDelay?: number;
  onOpen?: (ev: Event) => void;
  onMessage?: (data: any, raw: MessageEvent) => void;
  onClose?: (ev: CloseEvent) => void;
  onError?: (ev: Event) => void;
}

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    url,
    protocols,
    heartbeatInterval = 30000,
    heartbeatMessage = 'ping',
    reconnect = true,
    reconnectDelay = 2000,
    maxReconnectDelay = 30000,
  } = options;

  const ws = ref<WebSocket | null>(null);
  const isOpen = ref(false);
  const lastError = ref<Event | null>(null);
  let heartbeatTimer: number | null = null;
  let reconnectTimer: number | null = null;
  let currentDelay = reconnectDelay;
  let manuallyClosed = false;

  function clearHeartbeat() {
    if (heartbeatTimer) {
      window.clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
  }

  function startHeartbeat() {
    clearHeartbeat();
    heartbeatTimer = window.setInterval(() => {
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        try {
          ws.value.send(heartbeatMessage);
        } catch (e) {
          console.warn('心跳发送失败：', e);
        }
      }
    }, heartbeatInterval);
  }

  function scheduleReconnect() {
    if (!reconnect || manuallyClosed) return;
    if (reconnectTimer) window.clearTimeout(reconnectTimer);
    reconnectTimer = window.setTimeout(() => {
      connect();
      currentDelay = Math.min(currentDelay * 2, maxReconnectDelay);
    }, currentDelay);
  }

  function connect() {
    try {
      ws.value = new WebSocket(url, protocols);
    } catch (e) {
      lastError.value = e as Event;
      scheduleReconnect();
      return;
    }

    ws.value.onopen = (ev) => {
      isOpen.value = true;
      currentDelay = reconnectDelay;
      startHeartbeat();
      options.onOpen?.(ev);
    };
    ws.value.onmessage = (raw) => {
      let data: any = raw.data;
      try {
        if (typeof raw.data === 'string') {
          data = JSON.parse(raw.data);
        }
      } catch {
        // 非 JSON，按原始文本透传
      }
      options.onMessage?.(data, raw);
    };
    ws.value.onclose = (ev) => {
      isOpen.value = false;
      clearHeartbeat();
      options.onClose?.(ev);
      if (!manuallyClosed) scheduleReconnect();
    };
    ws.value.onerror = (ev) => {
      lastError.value = ev;
      options.onError?.(ev);
    };
  }

  function send(data: string | ArrayBuffer | Blob) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(data);
    } else {
      console.warn('WebSocket 未连接，无法发送：', data);
    }
  }

  function close(code = 1000, reason = 'manual') {
    manuallyClosed = true;
    clearHeartbeat();
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    ws.value?.close(code, reason);
  }

  connect();

  onBeforeUnmount(() => close());

  return { ws, isOpen, lastError, send, close, reconnect: connect };
}
