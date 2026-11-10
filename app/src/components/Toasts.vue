<template>
  <div class="toasts" aria-live="polite">
    <div v-for="t in ui.toasts" :key="t.id" class="toast" :class="t.type">
      <svg class="icon"><use :href="t.type === 'err' ? '#i-x' : t.type === 'gold' ? '#i-gift' : '#i-check'" /></svg>
      <span>{{ t.msg }}</span>
    </div>
  </div>
</template>

<script setup>
import { ui } from '../stores/ui';
</script>
