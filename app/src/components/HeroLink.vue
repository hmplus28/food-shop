<template>
  <!-- پیوند دکمه‌های بنر: مسیر داخلی با RouterLink، «/#بخش» با اسکرول، آدرس https با تب جدید -->
  <a v-if="external" :href="to" target="_blank" rel="noopener"><slot /></a>
  <RouterLink v-else :to="to"><slot /></RouterLink>
</template>

<script setup>
import { computed } from 'vue';
const props = defineProps({ to: { type: String, default: '/' } });
const external = computed(() => /^https:\/\//.test(props.to));
</script>
