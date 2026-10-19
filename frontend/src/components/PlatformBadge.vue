/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

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
