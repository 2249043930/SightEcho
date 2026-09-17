/**
 * stores/settings.ts
 * 用户偏好：语速、音量、唤醒、字号档位、TTS 自动播报
 */
import { defineStore } from 'pinia';
import { ref, watch } from 'vue';
import { storage } from '@/utils/storage';

export type FontScale = 'small' | 'medium' | 'large';

interface Settings {
  speed: number;        // 0.5 - 2.0
  volume: number;       // 0 - 100
  wakeEnabled: boolean;
  autoAnnounce: boolean; // 识别结果自动 TTS 播报
  fontScale: FontScale;
}

const KEY = 'sightecho_settings';
const DEFAULT: Settings = {
  speed: 1.0,
  volume: 80,
  wakeEnabled: true,
  autoAnnounce: true,
  fontScale: 'medium',
};

export const useSettingsStore = defineStore('settings', () => {
  const initial = storage.get<Settings>(KEY) || DEFAULT;
  const speed = ref<number>(initial.speed);
  const volume = ref<number>(initial.volume);
  const wakeEnabled = ref<boolean>(initial.wakeEnabled);
  const autoAnnounce = ref<boolean>(initial.autoAnnounce);
  const fontScale = ref<FontScale>(initial.fontScale);

  const fontSize = ref<string>(
    fontScale.value === 'small' ? '14px' : fontScale.value === 'large' ? '20px' : '16px',
  );

  function persist() {
    storage.set(KEY, {
      speed: speed.value,
      volume: volume.value,
      wakeEnabled: wakeEnabled.value,
      autoAnnounce: autoAnnounce.value,
      fontScale: fontScale.value,
    });
  }

  function setFontScale(s: FontScale) {
    fontScale.value = s;
    fontSize.value = s === 'small' ? '14px' : s === 'large' ? '20px' : '16px';
  }

  function reset() {
    speed.value = DEFAULT.speed;
    volume.value = DEFAULT.volume;
    wakeEnabled.value = DEFAULT.wakeEnabled;
    autoAnnounce.value = DEFAULT.autoAnnounce;
    fontScale.value = DEFAULT.fontScale;
    fontSize.value = '16px';
  }

  watch(
    [speed, volume, wakeEnabled, autoAnnounce, fontScale],
    () => persist(),
    { deep: true },
  );

  return {
    speed,
    volume,
    wakeEnabled,
    autoAnnounce,
    fontScale,
    fontSize,
    setFontScale,
    reset,
  };
});
