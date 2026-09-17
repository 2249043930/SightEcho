<script setup lang="ts">
/**
 * views/user/NotFound.vue
 * 404 页面
 */
import { useRouter } from 'vue-router';
const router = useRouter();
</script>

<template>
  <main class="not-found" role="main">
    <div class="nf-box">
      <h1 class="nf-title">404</h1>
      <p class="nf-text">您访问的页面不存在</p>
      <button class="nf-btn" @click="router.replace({ name: 'Home' })">
        返回首页
      </button>
    </div>
  </main>
</template>

<style lang="scss" scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-main;
  padding: 24px;
}
.nf-box {
  text-align: center;
  background: $bg-main;
  border-radius: $radius-xl;
  box-shadow: $shadow-md;
  padding: 48px 64px;
}
.nf-title {
  font-size: 96px;
  color: $accent;
  font-weight: 700;
  margin: 0 0 16px;
  line-height: 1;
}
.nf-text { color: $text-secondary; margin-bottom: 24px; }
.nf-btn {
  height: 48px;
  padding: 0 24px;
  background: $accent;
  color: #fff;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  cursor: pointer;
  font-weight: 600;
  &:hover { box-shadow: $shadow-md; }
  &:focus-visible { outline: 2px solid $text-main; outline-offset: 3px; }
}
</style>
