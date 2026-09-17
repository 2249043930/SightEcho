<script setup lang="ts">
/**
 * views/user/Login.vue
 * 登录页：邮箱 + 6 位验证码
 * 美术风格：新拟物派（Neumorphism）浅灰背景 + 装饰光斑
 * 笔记本：居中卡片 480px；手机：全屏表单
 *
 * 无障碍（A11y）功能：
 *   - 语音输入：邮箱/验证码均支持语音输入
 *   - TTS 状态播报：发送成功、错误等均自动播报
 *   - 字号档位：小/中/大（实时切换）
 *   - 高对比度模式：prefers-contrast 切换
 *   - 减弱动效：prefers-reduced-motion 切换
 *   - 键盘快捷键：Ctrl+Enter 提交、Alt+V 语音邮箱、Alt+C 语音验证码、Alt+H 帮助
 *   - 所有图标按钮均带 aria-label
 *   - 实时播报区（A11yAnnouncer）状态变化
 */
import { ref, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '@/stores/user';
import { useResponsive } from '@/composables/useResponsive';
import { useTTS } from '@/composables/useTTS';
import { useVoiceInput } from '@/composables/useVoiceInput';
import { sendEmailCode, loginByCode } from '@/api/auth';
import { getProfile } from '@/api/user';
import { ElMessage } from 'element-plus';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const { isMobile } = useResponsive();
const tts = useTTS();

// ========== 表单状态 ==========
const email = ref('');
const code = ref('');
const countdown = ref(0);
const sending = ref(false);
const submitting = ref(false);
const codeVisible = ref(false);
const emailRef = ref<HTMLInputElement | null>(null);
const codeInputRef = ref<HTMLInputElement | null>(null);

// ========== 无障碍设置 ==========
const fontScale = ref<'small' | 'medium' | 'large'>('medium');
const highContrast = ref(false);
const reduceMotion = ref(false);

const fontSizeMap = { small: 14, medium: 16, large: 20 };
const baseFontSize = computed(() => fontSizeMap[fontScale.value]);

watch([fontScale, highContrast, reduceMotion], () => {
  document.documentElement.style.fontSize = `${baseFontSize.value}px`;
  document.documentElement.classList.toggle('high-contrast', highContrast.value);
  document.documentElement.classList.toggle('reduce-motion', reduceMotion.value);
  localStorage.setItem(
    'a11y-settings',
    JSON.stringify({
      fontScale: fontScale.value,
      highContrast: highContrast.value,
      reduceMotion: reduceMotion.value,
    }),
  );
}, { immediate: true });

function loadA11ySettings() {
  try {
    const raw = localStorage.getItem('a11y-settings');
    if (!raw) return;
    const s = JSON.parse(raw);
    if (s.fontScale) fontScale.value = s.fontScale;
    if (typeof s.highContrast === 'boolean') highContrast.value = s.highContrast;
    if (typeof s.reduceMotion === 'boolean') reduceMotion.value = s.reduceMotion;
  } catch { /* ignore */ }
}

// ========== 弹窗 ==========
const helpDialogOpen = ref(false);
const agreementDialogOpen = ref(false);
const a11yPanelOpen = ref(false);

// ========== 校验 ==========
const validEmail = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value));
const canSubmit = computed(() => validEmail.value && code.value.length === 6);

let timer: number | null = null;

// ========== 实时播报 ==========
function announce(text: string, priority: 'polite' | 'assertive' = 'polite') {
  let announcer = document.getElementById('a11y-announcer');
  if (!announcer) {
    announcer = document.createElement('div');
    announcer.id = 'a11y-announcer';
    announcer.setAttribute('aria-live', 'assertive');
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    document.body.appendChild(announcer);
  }
  announcer.setAttribute('aria-live', priority);
  announcer.textContent = '';
  setTimeout(() => {
    if (announcer) announcer.textContent = text;
  }, 50);
}

// ========== 语音输入：邮箱 ==========
const emailVoice = useVoiceInput({
  onResult: (text, isFinal) => {
    // 自动清洗：去掉空格、常见的语音误识别字符
    const cleaned = text
      .replace(/\s+/g, '')
      .replace(/[，。、！？]/g, '')
      .replace(/at/g, '@')
      .replace(/[Ａ-Ｚａ-ｚ０-９]/g, (s) => String.fromCharCode(s.charCodeAt(0) - 0xFEE0));
    if (isFinal) {
      email.value = cleaned;
      announce(`已识别邮箱：${cleaned}`);
      tts.speak(`已识别邮箱：${cleaned}`);
      ElMessage.success('邮箱已识别');
    }
  },
  onError: (msg) => {
    ElMessage.warning(`语音识别失败：${msg}`);
    announce('邮箱语音识别失败');
  },
});

// ========== 语音输入：验证码 ==========
const codeVoice = useVoiceInput({
  onResult: (text, isFinal) => {
    // 验证码只取数字
    const digits = text.replace(/\D/g, '').slice(0, 6);
    if (isFinal && digits) {
      code.value = digits;
      announce(`已识别验证码：${digits.length} 位`);
      tts.speak(`已识别 ${digits.length} 位验证码`);
      ElMessage.success(`已识别 ${digits.length} 位验证码`);
    }
  },
  onError: (msg) => {
    ElMessage.warning(`语音识别失败：${msg}`);
    announce('验证码语音识别失败');
  },
});

function toggleEmailVoice() {
  if (emailVoice.isListening.value) {
    emailVoice.stop();
  } else {
    emailVoice.start();
    ElMessage.info('请说出您的邮箱地址，例如：zhang san at example dot com');
    tts.speak('请说出您的邮箱地址');
    announce('邮箱语音输入已启动');
  }
}

function toggleCodeVoice() {
  if (codeVoice.isListening.value) {
    codeVoice.stop();
  } else {
    codeVoice.start();
    ElMessage.info('请说出 6 位数字验证码');
    tts.speak('请说出 6 位数字验证码');
    announce('验证码语音输入已启动');
  }
}

// ========== 业务流程 ==========
async function handleSend() {
  if (!validEmail.value) {
    ElMessage.warning('请输入有效邮箱');
    tts.speak('请输入有效邮箱');
    emailRef.value?.focus();
    return;
  }
  if (countdown.value > 0) return;
  sending.value = true;
  try {
    const resp: any = await sendEmailCode({ email: email.value });
    // DEV 模式：邮件发送失败时后端直接在响应里返回验证码（仅本地联调）
    if (resp && resp.devOnly && resp.code) {
      code.value = resp.code;
      ElMessage.warning(`[DEV] 邮件发送失败，验证码已自动填入：${resp.code}`);
      announce(`开发模式：验证码 ${resp.code} 已填入`);
    } else {
      ElMessage.success('验证码已发送，请查收邮件');
      announce(`验证码已发送到 ${email.value}`);
    }
    tts.speak(`验证码已发送到 ${email.value}，请查收邮件`);
    countdown.value = 60;
    timer = window.setInterval(() => {
      countdown.value -= 1;
      if (countdown.value <= 0 && timer) {
        clearInterval(timer);
        timer = null;
      }
    }, 1000);
    setTimeout(() => codeInputRef.value?.focus(), 100);
  } catch (e: any) {
    const msg = e?.response?.data?.message || '发送失败，请重试';
    ElMessage.error(msg);
    announce(`验证码发送失败：${msg}`);
    tts.speak(`验证码发送失败：${msg}`);
  } finally {
    sending.value = false;
  }
}

async function handleSubmit() {
  if (!canSubmit.value) {
    ElMessage.warning('请输入有效邮箱和 6 位验证码');
    tts.speak('请输入有效邮箱和 6 位验证码');
    return;
  }
  submitting.value = true;
  announce('正在登录');
  tts.speak('正在登录，请稍候');
  try {
    const resp = await loginByCode({ email: email.value, code: code.value });
    userStore.setToken(resp.token, (resp.expiresIn || 7 * 24 * 3600) * 1000);
    try {
      const profile = await getProfile();
      userStore.setProfile(profile);
    } catch { /* ignore */ }
    ElMessage.success('登录成功');
    announce('登录成功，正在进入系统');
    tts.speak('登录成功，欢迎使用 SightEcho');
    const redirect = (route.query.redirect as string) || '/';
    setTimeout(() => {
      router.replace(redirect.startsWith('/') ? redirect : '/');
    }, 500);
  } catch (e: any) {
    const msg = e?.response?.data?.message || '登录失败，请检查验证码';
    ElMessage.error(msg);
    announce(`登录失败：${msg}`);
    tts.speak(`登录失败：${msg}`);
  } finally {
    submitting.value = false;
  }
}

function clearEmail() {
  email.value = '';
  announce('邮箱已清空');
  emailRef.value?.focus();
}

function toggleCodeVisibility() {
  codeVisible.value = !codeVisible.value;
  announce(codeVisible.value ? '验证码已显示' : '验证码已隐藏');
}

function openHelp() {
  helpDialogOpen.value = true;
  tts.speak('使用帮助，包含登录步骤和键盘快捷键');
}

function openAgreement() {
  agreementDialogOpen.value = true;
  tts.speak('用户协议与隐私政策');
}

function toggleA11yPanel() {
  a11yPanelOpen.value = !a11yPanelOpen.value;
  if (a11yPanelOpen.value) {
    tts.speak('无障碍设置面板已打开');
  }
}

function contactSupport() {
  ElMessage.info('支持邮箱：support@sightecho.com');
  tts.speak('支持邮箱：support at sightecho dot com');
}

function setFontScale(s: 'small' | 'medium' | 'large') {
  fontScale.value = s;
  const labels = { small: '小', medium: '中', large: '大' };
  announce(`字号已切换为${labels[s]}`);
  tts.speak(`字号已切换为${labels[s]}`);
}

function toggleContrast() {
  highContrast.value = !highContrast.value;
  announce(highContrast.value ? '已开启高对比度模式' : '已关闭高对比度模式');
  tts.speak(highContrast.value ? '已开启高对比度模式' : '已关闭高对比度模式');
}

function toggleMotion() {
  reduceMotion.value = !reduceMotion.value;
  announce(reduceMotion.value ? '已减弱动效' : '已恢复动效');
  tts.speak(reduceMotion.value ? '已减弱动效' : '已恢复动效');
}

// ========== 键盘快捷键 ==========
function handleGlobalKey(e: KeyboardEvent) {
  // Ctrl+Enter 提交
  if (e.ctrlKey && e.key === 'Enter') {
    e.preventDefault();
    handleSubmit();
    return;
  }
  // Alt+V 语音输入邮箱
  if (e.altKey && e.key.toLowerCase() === 'v') {
    e.preventDefault();
    toggleEmailVoice();
    return;
  }
  // Alt+C 语音输入验证码
  if (e.altKey && e.key.toLowerCase() === 'c') {
    e.preventDefault();
    toggleCodeVoice();
    return;
  }
  // Alt+H 帮助
  if (e.altKey && e.key.toLowerCase() === 'h') {
    e.preventDefault();
    openHelp();
    return;
  }
  // Alt+A 无障碍设置
  if (e.altKey && e.key.toLowerCase() === 'a') {
    e.preventDefault();
    toggleA11yPanel();
    return;
  }
  // Alt+S 发送验证码
  if (e.altKey && e.key.toLowerCase() === 's') {
    e.preventDefault();
    handleSend();
    return;
  }
}

onMounted(async () => {
  loadA11ySettings();
  await nextTick();
  emailRef.value?.focus();
  // 自动检测系统偏好
  if (window.matchMedia('(prefers-contrast: more)').matches) {
    highContrast.value = true;
  }
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    reduceMotion.value = true;
  }
  // 欢迎播报
  setTimeout(() => {
    announce('SightEcho 昭视智伴 登录页，按 Alt 加 H 听取使用帮助');
    tts.speak('欢迎使用 SightEcho 昭视智伴。按 Alt 加 H 听取使用帮助。');
  }, 600);
  window.addEventListener('keydown', handleGlobalKey);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalKey);
  if (timer) clearInterval(timer);
  emailVoice.stop();
  codeVoice.stop();
});
</script>

<template>
  <div class="login-page">
    <!-- 新拟物派装饰：浅灰光斑 -->
    <div class="bg-orb bg-orb-1" aria-hidden="true" />
    <div class="bg-orb bg-orb-2" aria-hidden="true" />
    <div class="bg-orb bg-orb-3" aria-hidden="true" />

    <!-- 顶部辅助工具栏（无障碍图标按钮） -->
    <nav class="top-toolbar" aria-label="辅助功能">
      <button
        class="icon-btn"
        type="button"
        aria-label="打开使用帮助（快捷键 Alt 加 H）"
        @click="openHelp"
      >
        <el-icon :size="20"><QuestionFilled /></el-icon>
      </button>
      <span class="toolbar-title" aria-hidden="true">SightEcho 昭视智伴</span>
      <button
        class="icon-btn a11y-toggle"
        type="button"
        :aria-label="`无障碍设置（快捷键 Alt 加 A）${a11yPanelOpen ? '，已展开' : ''}`"
        :aria-expanded="a11yPanelOpen"
        aria-haspopup="dialog"
        @click="toggleA11yPanel"
      >
        <el-icon :size="20"><Setting /></el-icon>
      </button>
      <button
        class="icon-btn"
        type="button"
        aria-label="联系技术支持（快捷键 Alt 加 H 已用于帮助，按钮直接联系）"
        @click="contactSupport"
      >
        <el-icon :size="20"><Service /></el-icon>
      </button>
    </nav>

    <main class="login-wrap" :class="{ mobile: isMobile }" id="main-content">
      <header class="login-header">
        <div class="brand-icon" aria-hidden="true">
          <el-icon :size="48"><View /></el-icon>
        </div>
        <h1 class="brand-title">SightEcho</h1>
        <p class="brand-subtitle">昭视智伴 · 视障场景智能感知系统</p>
      </header>

      <!-- 无障碍面板（折叠展开） -->
      <transition name="slide">
        <section v-if="a11yPanelOpen" class="a11y-panel" role="region" aria-label="无障碍设置">
          <h2 class="panel-title">
            <el-icon :size="18" aria-hidden="true"><Setting /></el-icon>
            无障碍设置
          </h2>
          <div class="panel-row">
            <span class="panel-label">字号档位</span>
            <el-radio-group
              :model-value="fontScale"
              @change="setFontScale"
              aria-label="字号档位切换"
            >
              <el-radio-button value="small" aria-label="小号字号 14px">小</el-radio-button>
              <el-radio-button value="medium" aria-label="中号字号 16px">中</el-radio-button>
              <el-radio-button value="large" aria-label="大号字号 20px">大</el-radio-button>
            </el-radio-group>
          </div>
          <div class="panel-row">
            <span class="panel-label">高对比度</span>
            <el-switch
              :model-value="highContrast"
              @change="toggleContrast"
              aria-label="高对比度模式开关"
            />
          </div>
          <div class="panel-row">
            <span class="panel-label">减弱动效</span>
            <el-switch
              :model-value="reduceMotion"
              @change="toggleMotion"
              aria-label="减弱动效开关"
            />
          </div>
          <p class="panel-hint">
            <el-icon :size="14" aria-hidden="true"><InfoFilled /></el-icon>
            设置会自动保存到本地，下次访问自动应用
          </p>
        </section>
      </transition>

      <section
        class="login-card"
        role="form"
        aria-label="邮箱登录表单"
      >
        <h2 class="card-title">
          <el-icon :size="20" aria-hidden="true"><User /></el-icon>
          邮箱登录
        </h2>
        <p class="card-desc">
          输入邮箱获取 6 位验证码，登录或注册新账号
        </p>

        <form @submit.prevent="handleSubmit">
          <!-- 邮箱输入 -->
          <div class="field">
            <label for="email" class="label">
              <el-icon :size="16" aria-hidden="true"><Message /></el-icon>
              邮箱地址
              <span class="required" aria-label="必填">*</span>
            </label>
            <div class="input-wrap" :class="{ 'voice-active': emailVoice.isListening.value }">
              <el-input
                id="email"
                ref="emailRef"
                v-model="email"
                type="email"
                size="large"
                autocomplete="email"
                placeholder="example@email.com"
                :aria-invalid="email && !validEmail"
                aria-errormessage="email-error"
                inputmode="email"
                aria-describedby="email-voice-status"
              >
                <template #prefix>
                  <el-icon :size="18" aria-hidden="true"><Message /></el-icon>
                </template>
              </el-input>
              <span id="email-voice-status" class="sr-only" aria-live="polite">
                {{ emailVoice.isListening.value ? '正在听取邮箱' : '邮箱输入框' }}
              </span>
              <!-- 语音输入按钮 -->
              <button
                type="button"
                class="input-action voice"
                :class="{ listening: emailVoice.isListening.value }"
                :aria-label="emailVoice.isListening.value ? '停止邮箱语音输入' : '使用语音输入邮箱（快捷键 Alt 加 V）'"
                :aria-pressed="emailVoice.isListening.value"
                :title="emailVoice.isListening.value ? '停止' : '语音输入邮箱'"
                @click="toggleEmailVoice"
              >
                <el-icon :size="16">
                  <component :is="emailVoice.isListening.value ? 'VideoPause' : 'Microphone'" />
                </el-icon>
              </button>
              <!-- 清空按钮 -->
              <button
                v-if="email"
                type="button"
                class="input-action"
                aria-label="清空邮箱"
                title="清空"
                @click="clearEmail"
              >
                <el-icon :size="16"><CircleClose /></el-icon>
              </button>
            </div>
            <p v-if="emailVoice.isListening.value" class="voice-hint" aria-live="polite">
              <span class="voice-dot" />
              正在听… {{ emailVoice.interim.value }}
            </p>
            <span
              v-if="email && !validEmail"
              id="email-error"
              role="alert"
              class="error-text"
            >
              <el-icon :size="14" aria-hidden="true"><WarningFilled /></el-icon>
              请输入有效邮箱地址
            </span>
          </div>

          <!-- 验证码输入 -->
          <div class="field">
            <label for="code" class="label">
              <el-icon :size="16" aria-hidden="true"><Key /></el-icon>
              验证码
              <span class="required" aria-label="必填">*</span>
            </label>
            <div class="code-row">
              <div class="input-wrap" :class="{ 'voice-active': codeVoice.isListening.value }" style="flex: 1;">
                <el-input
                  id="code"
                  ref="codeInputRef"
                  v-model="code"
                  size="large"
                  maxlength="6"
                  :type="codeVisible ? 'text' : 'password'"
                  placeholder="6 位验证码"
                  autocomplete="one-time-code"
                  inputmode="numeric"
                  :aria-invalid="code && code.length !== 6"
                  aria-describedby="code-voice-status"
                >
                  <template #prefix>
                    <el-icon :size="18" aria-hidden="true"><Key /></el-icon>
                  </template>
                </el-input>
                <span id="code-voice-status" class="sr-only" aria-live="polite">
                  {{ codeVoice.isListening.value ? '正在听取验证码' : '验证码输入框' }}
                </span>
                <!-- 语音输入按钮 -->
                <button
                  type="button"
                  class="input-action voice"
                  :class="{ listening: codeVoice.isListening.value }"
                  :aria-label="codeVoice.isListening.value ? '停止验证码语音输入' : '使用语音输入验证码（快捷键 Alt 加 C）'"
                  :aria-pressed="codeVoice.isListening.value"
                  :title="codeVoice.isListening.value ? '停止' : '语音输入验证码'"
                  @click="toggleCodeVoice"
                >
                  <el-icon :size="16">
                    <component :is="codeVoice.isListening.value ? 'VideoPause' : 'Microphone'" />
                  </el-icon>
                </button>
                <!-- 显示/隐藏按钮 -->
                <button
                  type="button"
                  class="input-action"
                  :aria-label="codeVisible ? '隐藏验证码' : '显示验证码'"
                  :aria-pressed="codeVisible"
                  :title="codeVisible ? '隐藏' : '显示'"
                  @click="toggleCodeVisibility"
                >
                  <el-icon :size="16">
                    <component :is="codeVisible ? 'Hide' : 'View'" />
                  </el-icon>
                </button>
              </div>
              <button
                type="button"
                class="send-btn"
                :disabled="!validEmail || countdown > 0 || sending"
                :aria-label="countdown > 0 ? `${countdown} 秒后可重新发送验证码` : '发送验证码到邮箱（快捷键 Alt 加 S）'"
                @click="handleSend"
              >
                <el-icon :size="16" aria-hidden="true">
                  <component :is="countdown > 0 ? 'Clock' : 'Promotion'" />
                </el-icon>
                <span>{{ countdown > 0 ? `${countdown}s` : '发送' }}</span>
              </button>
            </div>
            <p v-if="codeVoice.isListening.value" class="voice-hint" aria-live="polite">
              <span class="voice-dot" />
              正在听… {{ codeVoice.interim.value }}
            </p>
          </div>

          <!-- 登录 -->
          <button
            type="submit"
            class="submit-btn"
            :disabled="!canSubmit || submitting"
            :aria-busy="submitting"
            aria-label="登录或注册（快捷键 Ctrl 加 Enter）"
          >
            <el-icon :size="20" aria-hidden="true">
              <component :is="submitting ? 'Loading' : 'Right'" />
            </el-icon>
            <span>{{ submitting ? '登录中…' : '登录 / 注册' }}</span>
          </button>
        </form>

        <p class="footer-text">
          未注册邮箱将自动创建账号；登录即代表
          <button class="link-btn" type="button" aria-label="查看用户协议" @click="openAgreement">
            《用户协议》
          </button>
          和
          <button class="link-btn" type="button" aria-label="查看隐私政策" @click="openAgreement">
            《隐私政策》
          </button>
        </p>
      </section>

      <!-- 底部快捷功能区：图标按钮组（4 个，全部带图标） -->
      <nav class="quick-actions" aria-label="快捷功能">
        <button class="action-card" type="button" @click="toggleEmailVoice" aria-label="语音输入邮箱（快捷键 Alt 加 V）">
          <div class="action-icon" :class="{ active: emailVoice.isListening.value }">
            <el-icon :size="22" aria-hidden="true">
              <component :is="emailVoice.isListening.value ? 'VideoPause' : 'Microphone'" />
            </el-icon>
          </div>
          <span class="action-label">语音邮箱</span>
        </button>
        <button class="action-card" type="button" @click="openHelp" aria-label="使用帮助（快捷键 Alt 加 H）">
          <div class="action-icon">
            <el-icon :size="22" aria-hidden="true"><Document /></el-icon>
          </div>
          <span class="action-label">使用说明</span>
        </button>
        <button class="action-card" type="button" @click="contactSupport" aria-label="联系客服">
          <div class="action-icon">
            <el-icon :size="22" aria-hidden="true"><ChatLineRound /></el-icon>
          </div>
          <span class="action-label">联系客服</span>
        </button>
        <button class="action-card" type="button" @click="openAgreement" aria-label="服务条款">
          <div class="action-icon">
            <el-icon :size="22" aria-hidden="true"><Postcard /></el-icon>
          </div>
          <span class="action-label">服务条款</span>
        </button>
      </nav>

      <!-- 快捷键提示 -->
      <section class="shortcut-hint" aria-label="键盘快捷键">
        <h3 class="shortcut-title">
          <el-icon :size="16" aria-hidden="true"><Key /></el-icon>
          键盘快捷键
        </h3>
        <ul class="shortcut-list">
          <li><kbd>Alt + V</kbd> 语音输入邮箱</li>
          <li><kbd>Alt + C</kbd> 语音输入验证码</li>
          <li><kbd>Alt + S</kbd> 发送验证码</li>
          <li><kbd>Alt + H</kbd> 打开帮助</li>
          <li><kbd>Alt + A</kbd> 无障碍设置</li>
          <li><kbd>Ctrl + Enter</kbd> 提交登录</li>
        </ul>
      </section>
    </main>

    <!-- 帮助弹窗 -->
    <el-dialog v-model="helpDialogOpen" title="使用帮助" width="480px" aria-label="使用帮助">
      <div class="help-content">
        <h3>登录步骤</h3>
        <ol>
          <li>输入您常用的邮箱地址（可使用语音输入）</li>
          <li>点击「发送」获取 6 位验证码</li>
          <li>查收邮件，输入 6 位验证码（可使用语音输入）</li>
          <li>点击「登录 / 注册」进入系统</li>
        </ol>
        <h3>语音输入说明</h3>
        <ul>
          <li>邮箱：直接说出邮箱地址，例如「zhangsan at example dot com」</li>
          <li>验证码：只识别数字，请清晰说出 6 位数字</li>
        </ul>
        <h3>键盘快捷键</h3>
        <ul>
          <li><kbd>Tab</kbd> / <kbd>Shift+Tab</kbd>：在表单元素间切换</li>
          <li><kbd>Alt + V</kbd>：语音输入邮箱</li>
          <li><kbd>Alt + C</kbd>：语音输入验证码</li>
          <li><kbd>Alt + S</kbd>：发送验证码</li>
          <li><kbd>Alt + H</kbd>：打开帮助</li>
          <li><kbd>Alt + A</kbd>：无障碍设置</li>
          <li><kbd>Ctrl + Enter</kbd>：提交登录</li>
          <li><kbd>Esc</kbd>：关闭弹窗</li>
        </ul>
      </div>
    </el-dialog>

    <!-- 协议弹窗 -->
    <el-dialog v-model="agreementDialogOpen" title="用户协议与隐私政策" width="520px" aria-label="用户协议与隐私政策">
      <div class="help-content">
        <h3>用户协议</h3>
        <p>本系统面向视障人士提供场景智能感知服务。使用本服务即表示您同意遵守相关法律法规及本协议条款。</p>
        <h3>隐私政策</h3>
        <p>我们重视您的隐私，识别图片仅在处理时临时存储，处理完成后立即删除，不会用于其他用途。</p>
        <h3>数据安全</h3>
        <p>所有数据传输使用 HTTPS 加密，账号密码采用业界标准加密存储。</p>
      </div>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.login-page {
  position: relative;
  min-height: 100vh;
  background: $bg-main;
  overflow: hidden;
  padding: 24px;
}

// 装饰光斑
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  pointer-events: none;
  z-index: 0;
}
.bg-orb-1 {
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, rgba(109, 93, 252, 0.25), transparent 70%);
  top: -120px;
  right: -120px;
}
.bg-orb-2 {
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(78, 205, 196, 0.22), transparent 70%);
  bottom: -100px;
  left: -100px;
}
.bg-orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(255, 180, 84, 0.18), transparent 70%);
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
}
@include mobile {
  .bg-orb-1 { width: 320px; height: 320px; }
  .bg-orb-2 { width: 240px; height: 240px; }
  .bg-orb-3 { display: none; }
}

// 顶部辅助工具栏
.top-toolbar {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  max-width: 720px;
  margin: 0 auto 16px;
  gap: 12px;
}
.toolbar-title {
  font-size: 16px;
  font-weight: 600;
  color: $text-secondary;
  letter-spacing: 0.05em;
  margin-right: auto;
}
@include mobile {
  .toolbar-title { display: none; }
}
.icon-btn {
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: $bg-main;
  border: 0;
  border-radius: 50%;
  box-shadow: 4px 4px 8px $shadow-dark, -4px -4px 8px $shadow-light;
  color: $text-main;
  cursor: pointer;
  transition: $transition-base;
  &:hover {
    box-shadow: 2px 2px 4px $shadow-dark, -2px -2px 4px $shadow-light;
  }
  &:active, &:focus-visible {
    box-shadow: inset 4px 4px 8px $shadow-dark, inset -4px -4px 8px $shadow-light;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
  &.a11y-toggle[aria-expanded='true'] {
    color: $accent;
    box-shadow: inset 4px 4px 8px $shadow-dark, inset -4px -4px 8px $shadow-light;
  }
}

.login-wrap {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 520px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
@include mobile {
  .login-page { padding: 0; }
  .login-wrap { max-width: 100%; min-height: 100vh; padding: 24px 20px; }
}
.login-header {
  text-align: center;
}
.brand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 88px;
  height: 88px;
  background: $bg-main;
  border-radius: 50%;
  box-shadow: 8px 8px 16px $shadow-dark, -8px -8px 16px $shadow-light;
  color: $accent;
  margin-bottom: 16px;
}
.brand-title {
  font-size: 36px;
  font-weight: 700;
  color: $text-main;
  margin: 0;
  letter-spacing: 0.02em;
}
.brand-subtitle {
  font-size: 14px;
  color: $text-secondary;
  margin: 4px 0 0;
}

// 无障碍面板
.a11y-panel {
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: 6px 6px 12px $shadow-dark, -6px -6px 12px $shadow-light;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: $text-main;
  margin: 0;
}
.panel-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 48px;
}
@include mobile { .panel-row { flex-direction: column; align-items: flex-start; } }
.panel-label {
  font-size: 15px;
  color: $text-main;
  font-weight: 500;
}
.panel-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: $text-muted;
  margin: 0;
}
.slide-enter-active, .slide-leave-active {
  transition: all 200ms ease;
}
.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.login-card {
  background: $bg-main;
  border-radius: $radius-xl;
  box-shadow: 12px 12px 24px $shadow-dark, -12px -12px 24px $shadow-light;
  padding: 32px;
  border: 0;
}
@include mobile {
  .login-card { padding: 24px 20px; }
}
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 22px;
  font-weight: 600;
  color: $text-main;
  margin: 0 0 8px;
}
.card-desc {
  font-size: 14px;
  color: $text-secondary;
  margin: 0 0 24px;
}
.field { margin-bottom: 18px; }
.label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: $text-main;
  margin-bottom: 8px;
}
.required { color: $color-danger; font-weight: 700; }

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  transition: $transition-base;
  &.voice-active :deep(.el-input__wrapper) {
    box-shadow: inset 2px 2px 4px $shadow-dark, inset -2px -2px 4px $shadow-light, 0 0 0 2px $color-danger !important;
  }
}
.input-action {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: $bg-main;
  border: 0;
  border-radius: 50%;
  box-shadow: 2px 2px 4px $shadow-dark, -2px -2px 4px $shadow-light;
  color: $text-secondary;
  cursor: pointer;
  z-index: 2;
  transition: $transition-base;
  &:hover { color: $accent; }
  &:active, &:focus-visible {
    box-shadow: inset 2px 2px 4px $shadow-dark, inset -2px -2px 4px $shadow-light;
    outline: 2px solid $accent;
    outline-offset: 1px;
  }
  &.voice {
    color: $text-secondary;
    right: 52px;
  }
  &.voice.listening {
    color: #fff;
    background: $color-danger;
    box-shadow: 4px 4px 8px $shadow-dark, -4px -4px 8px $shadow-light;
    animation: pulse 1.2s ease-in-out infinite;
  }
  &.voice.listening:hover { color: #fff; }
}
.input-action:not(.voice) { right: 8px; }
:deep(.el-input) { flex: 1; }
:deep(.el-input__inner) { padding-right: 96px !important; }
.code-row :deep(.el-input__inner) { padding-right: 96px !important; }

@keyframes pulse {
  0%, 100% { transform: translateY(-50%) scale(1); }
  50% { transform: translateY(-50%) scale(1.08); }
}

.voice-hint {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: $color-danger;
  margin: 6px 0 0;
  font-weight: 500;
}
.voice-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: $color-danger;
  border-radius: 50%;
  animation: blink 1s ease-in-out infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.error-text {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: $color-danger;
  margin-top: 6px;
}

.code-row {
  display: flex;
  gap: 8px;
  align-items: stretch;
}
.send-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 48px;
  padding: 0 16px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: 4px 4px 8px $shadow-dark, -4px -4px 8px $shadow-light;
  color: $text-main;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  transition: $transition-base;
  &:hover:not(:disabled) {
    box-shadow: 2px 2px 4px $shadow-dark, -2px -2px 4px $shadow-light;
    color: $accent;
  }
  &:active:not(:disabled), &:focus-visible {
    box-shadow: inset 4px 4px 8px $shadow-dark, inset -4px -4px 8px $shadow-light;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 52px;
  margin-top: 8px;
  background: $accent;
  color: #fff;
  border: 0;
  border-radius: $radius-md;
  box-shadow: 6px 6px 12px $shadow-dark, -6px -6px 12px $shadow-light;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: $transition-base;
  &:hover:not(:disabled) {
    box-shadow: 4px 4px 8px $shadow-dark, -4px -4px 8px $shadow-light;
  }
  &:active:not(:disabled), &:focus-visible {
    box-shadow: inset 4px 4px 8px $accent-active, inset -4px -4px 8px #8a7dff;
    outline: 2px solid $text-main;
    outline-offset: 3px;
  }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
.footer-text {
  margin: 16px 0 0;
  font-size: 12px;
  color: $text-muted;
  text-align: center;
  line-height: 1.5;
}
.link-btn {
  background: none;
  border: 0;
  padding: 0;
  color: $accent;
  font: inherit;
  cursor: pointer;
  text-decoration: underline;
  &:hover { color: $accent-hover; }
  &:focus-visible { outline: 2px solid $accent; outline-offset: 2px; border-radius: 2px; }
}

// 底部快捷功能区
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
@include mobile {
  .quick-actions {
    grid-template-columns: repeat(2, 1fr);
  }
}
.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 8px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: 4px 4px 8px $shadow-dark, -4px -4px 8px $shadow-light;
  color: $text-main;
  cursor: pointer;
  transition: $transition-base;
  min-height: 96px;
  &:hover {
    box-shadow: 2px 2px 4px $shadow-dark, -2px -2px 4px $shadow-light;
  }
  &:active, &:focus-visible {
    box-shadow: inset 4px 4px 8px $shadow-dark, inset -4px -4px 8px $shadow-light;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
}
.action-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-main;
  border-radius: 50%;
  box-shadow: inset 3px 3px 6px $shadow-dark, inset -3px -3px 6px $shadow-light;
  color: $accent;
  &.active {
    color: #fff;
    background: $color-danger;
    box-shadow: 3px 3px 6px $shadow-dark, -3px -3px 6px $shadow-light;
    animation: pulse 1.2s ease-in-out infinite;
  }
}
.action-label {
  font-size: 12px;
  color: $text-secondary;
  font-weight: 500;
}

// 快捷键提示
.shortcut-hint {
  background: $bg-main;
  border-radius: $radius-md;
  box-shadow: inset 4px 4px 8px $shadow-dark, inset -4px -4px 8px $shadow-light;
  padding: 16px 20px;
}
.shortcut-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: $text-secondary;
  margin: 0 0 8px;
  font-weight: 600;
}
.shortcut-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px 12px;
  font-size: 12px;
  color: $text-muted;
  li { line-height: 1.6; }
}
@include mobile {
  .shortcut-list { grid-template-columns: 1fr; }
}
kbd {
  display: inline-block;
  padding: 1px 6px;
  background: $bg-elevated;
  border-radius: 4px;
  box-shadow: inset 1px 1px 2px $shadow-dark, inset -1px -1px 2px $shadow-light;
  font-family: monospace;
  font-size: 11px;
  color: $text-main;
  margin-right: 4px;
}

.help-content {
  color: $text-main;
  line-height: 1.7;
  h3 {
    font-size: 16px;
    color: $text-main;
    margin: 16px 0 8px;
    &:first-child { margin-top: 0; }
  }
  p { margin: 0 0 8px; color: $text-secondary; }
  ol, ul { padding-left: 24px; margin: 8px 0; }
  li { margin-bottom: 4px; color: $text-secondary; }
  kbd {
    display: inline-block;
    padding: 2px 8px;
    background: $bg-elevated;
    border-radius: 4px;
    box-shadow: inset 1px 1px 2px $shadow-dark, inset -1px -1px 2px $shadow-light;
    font-family: monospace;
    font-size: 12px;
    color: $text-main;
  }
}

// 全局高对比度（无障碍面板切换时）
:global(html.high-contrast) {
  --bg-main: #ffffff;
  --text-main: #000000;
  --accent: #0040ff;
}
:global(html.high-contrast) .login-page { background: #ffffff; }
:global(html.high-contrast) .login-card,
:global(html.high-contrast) .icon-btn,
:global(html.high-contrast) .a11y-panel,
:global(html.high-contrast) .send-btn,
:global(html.high-contrast) .action-card,
:global(html.high-contrast) .shortcut-hint {
  background: #ffffff !important;
  color: #000000 !important;
  box-shadow: 0 0 0 2px #000000 !important;
}
:global(html.high-contrast) .brand-title,
:global(html.high-contrast) .card-title,
:global(html.high-contrast) .label,
:global(html.high-contrast) .panel-label { color: #000 !important; }
:global(html.high-contrast) .submit-btn { box-shadow: 0 0 0 2px #0040ff !important; }

// 全局减弱动效
:global(html.reduce-motion) *,
:global(html.reduce-motion) *::before,
:global(html.reduce-motion) *::after {
  animation-duration: 0.01ms !important;
  animation-iteration-count: 1 !important;
  transition-duration: 0.01ms !important;
}
</style>
