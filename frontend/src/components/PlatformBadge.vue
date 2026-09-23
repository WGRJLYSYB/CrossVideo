<template>
  <span
    class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border"
    :class="[meta.bgColor, meta.color, meta.borderColor]"
  >
    {{ meta.name }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getPlatformMeta } from '@/utils/format'

const props = defineProps<{
  siteHost?: string | null
}>()

const meta = computed(() => getPlatformMeta(props.siteHost))
</script>
