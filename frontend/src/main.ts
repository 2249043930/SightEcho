/**
 * main.ts
 * 应用入口：注册 Pinia、Router、Element Plus、初始化 rem 适配
 */
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';

import App from './App.vue';
import router from './router';
import { initFlexible } from './utils/flexiable';

import './assets/styles/index.scss';

const app = createApp(App);

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component as any);
}

app.use(createPinia());
app.use(router);
app.use(ElementPlus);

// 初始化 rem 适配
initFlexible();

app.mount('#app');
