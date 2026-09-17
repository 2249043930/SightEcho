/**
 * stores/user.ts
 * 用户信息、JWT
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { storage } from '@/utils/storage';

export interface UserProfile {
  id: string;
  email: string;
  nickname?: string;
  avatar?: string;
  role: 'user' | 'admin';
  createdAt?: string;
}

const TOKEN_KEY = 'sightecho_token';
const PROFILE_KEY = 'sightecho_profile';

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(storage.get<string>(TOKEN_KEY) || '');
  const profile = ref<UserProfile | null>(storage.get<UserProfile>(PROFILE_KEY) || null);

  const isLoggedIn = computed(() => !!token.value);
  const isAdmin = computed(() => profile.value?.role === 'admin');

  function setToken(t: string, expiresIn?: number) {
    token.value = t;
    storage.set(TOKEN_KEY, t, expiresIn);
  }

  function setProfile(p: UserProfile) {
    profile.value = p;
    storage.set(PROFILE_KEY, p);
  }

  function logout() {
    token.value = '';
    profile.value = null;
    storage.remove(TOKEN_KEY);
    storage.remove(PROFILE_KEY);
  }

  return {
    token,
    profile,
    isLoggedIn,
    isAdmin,
    setToken,
    setProfile,
    logout,
  };
});
