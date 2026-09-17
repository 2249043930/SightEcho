/**
 * utils/audio.ts
 * 音频格式转换工具：Blob <-> ArrayBuffer、AudioBuffer 采样、WAV 编码、base64
 */

/** Blob 转 ArrayBuffer */
export function blobToArrayBuffer(blob: Blob): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as ArrayBuffer);
    reader.onerror = () => reject(reader.error);
    reader.readAsArrayBuffer(blob);
  });
}

/** ArrayBuffer 转 Blob */
export function arrayBufferToBlob(buffer: ArrayBuffer, type = 'audio/wav'): Blob {
  return new Blob([buffer], { type });
}

/** ArrayBuffer 转 base64 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

/** base64 转 ArrayBuffer */
export function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = window.atob(base64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * 将 AudioBuffer 编码为 16-bit PCM WAV
 * 主要用于流式录音末尾补齐 WAV 头以便后端 ASR 接收
 */
export function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
  const numOfChannels = buffer.numberOfChannels;
  const length = buffer.length * numOfChannels * 2 + 44;
  const out = new ArrayBuffer(length);
  const view = new DataView(out);
  const channels: Float32Array[] = [];
  let offset = 0;
  let pos = 0;

  // 写 WAV 文件头
  const setUint32 = (data: number) => {
    view.setUint32(pos, data, true);
    pos += 4;
  };
  const setUint16 = (data: number) => {
    view.setUint16(pos, data, true);
    pos += 2;
  };

  // RIFF chunk descriptor
  setUint32(0x46464952); // "RIFF"
  setUint32(length - 8);
  setUint32(0x45564157); // "WAVE"

  // fmt sub-chunk
  setUint32(0x20746d66); // "fmt "
  setUint16(16); // PCM chunk size
  setUint16(1); // format = PCM
  setUint16(numOfChannels);
  setUint32(buffer.sampleRate);
  setUint32(buffer.sampleRate * numOfChannels * 2); // byte rate
  setUint16(numOfChannels * 2); // block align
  setUint16(16); // bits per sample

  // data sub-chunk
  setUint32(0x61746164); // "data"
  setUint32(length - pos - 4);

  // 写入交错 PCM 数据
  for (let i = 0; i < buffer.numberOfChannels; i++) {
    channels.push(buffer.getChannelData(i));
  }
  while (offset < buffer.length) {
    for (let i = 0; i < numOfChannels; i++) {
      let sample = Math.max(-1, Math.min(1, channels[i][offset]));
      sample = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
      view.setInt16(pos, sample, true);
      pos += 2;
    }
    offset++;
  }
  return out;
}

/** 将麦克风 MediaStream 转 PCM 16kHz 单声道（通过 AudioContext） */
export async function resampleTo16kPCM(stream: MediaStream): Promise<AudioBuffer> {
  const AC = window.AudioContext || (window as any).webkitAudioContext;
  const audioCtx: AudioContext = new AC({ sampleRate: 16000 });
  const source = audioCtx.createMediaStreamSource(stream);
  const bufferSize = 4096;
  const processor = audioCtx.createScriptProcessor(bufferSize, 1, 1);
  const buffers: Float32Array[] = [];
  source.connect(processor);
  processor.connect(audioCtx.destination);

  return new Promise((resolve) => {
    processor.onaudioprocess = (e) => {
      const channel = e.inputBuffer.getChannelData(0);
      buffers.push(new Float32Array(channel));
    };
    // 用户需要外部停止录音后调用 resolve
    (processor as any)._stop = () => {
      processor.disconnect();
      source.disconnect();
      const total = buffers.reduce((acc, cur) => acc + cur.length, 0);
      const result = new Float32Array(total);
      let offset = 0;
      buffers.forEach((b) => {
        result.set(b, offset);
        offset += b.length;
      });
      const out = audioCtx.createBuffer(1, result.length, 16000);
      out.copyToChannel(result, 0);
      audioCtx.close();
      resolve(out);
    };
  });
}

/** 播放 base64 音频 */
export function playBase64Audio(base64: string, mime = 'audio/mp3'): HTMLAudioElement {
  const audio = new Audio(`data:${mime};base64,${base64}`);
  audio.play().catch((err) => {
    console.error('音频播放失败：', err);
  });
  return audio;
}
