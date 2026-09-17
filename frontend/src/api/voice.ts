/**
 * api/voice.ts
 * 语音：ASR / TTS WebSocket
 */
import request from './request';

export interface AsrTokenResp {
  token: string;
  url: string;
}
export interface TtsParams {
  text: string;
  voice?: string;
  speed?: number;
  volume?: number;
}
export interface TtsResp {
  audioUrl: string;
  duration: number;
}

/** 申请 ASR 临时 token */
export function getAsrToken() {
  return request.post<any, AsrTokenResp>('/voice/asr/token');
}

/** 申请 TTS 临时 token */
export function getTtsToken() {
  return request.post<any, AsrTokenResp>('/voice/tts/token');
}

/** 直接请求 TTS，返回音频 URL */
export function ttsOnce(params: TtsParams) {
  return request.post<any, TtsResp>('/voice/tts', params);
}
