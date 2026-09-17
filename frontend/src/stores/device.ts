/**
 * stores/device.ts
 * 当前设备类型（mobile / laptop）
 */
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useResponsive, type DeviceType } from '@/composables/useResponsive';

export const useDeviceStore = defineStore('device', () => {
  const device = ref<DeviceType>('laptop');
  const width = ref(1920);
  const height = ref(1080);

  function bind() {
    const r = useResponsive();
    device.value = r.device.value;
    width.value = r.width.value;
    height.value = r.height.value;
  }

  return { device, width, height, bind };
});
