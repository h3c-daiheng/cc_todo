<template>
  <app-layout v-if="showLayout">
    <router-view />
  </app-layout>
  <router-view v-else />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from './stores/user.js'
import AppLayout from './components/AppLayout.vue'

const route = useRoute()
const store = useUserStore()

const showLayout = computed(() => {
  return store.isLoggedIn && !route.meta.public
})
</script>

<style>
:root {
  --primary: #6366F1;
  --primary-hover: #4F46E5;
  --primary-light: #EEF2FF;
  --primary-border: #C7D2FE;
  --sidebar-bg: #1E1B4B;
  --sidebar-active: rgba(99,102,241,0.3);
  --page-bg: #F8FAFC;
  --card-bg: #FFFFFF;
  --card-inner-bg: #FAFAFA;
  --border: #E2E8F0;
  --text-primary: #1E1B4B;
  --text-secondary: #64748B;
  --text-muted: #94A3B8;
  --success: #10B981;
  --warning: #F59E0B;
  --danger: #EF4444;

  /* Override Element Plus primary color to match design system */
  --el-color-primary: #6366F1;
  --el-color-primary-light-3: #818CF8;
  --el-color-primary-light-5: #A5B4FC;
  --el-color-primary-light-7: #C7D2FE;
  --el-color-primary-light-8: #E0E7FF;
  --el-color-primary-light-9: #EEF2FF;
  --el-color-primary-dark-2: #4F46E5;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--page-bg);
  font-family: 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  color: var(--text-primary);
}
</style>
