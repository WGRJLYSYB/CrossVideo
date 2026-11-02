<template>
  <section class="space-y-5">
    <div>
      <h1 class="text-2xl font-bold">用户管理</h1>
      <p class="mt-1 text-sm text-slate-500">查看普通用户和超管账号；普通用户可停用或重新启用。</p>
    </div>

    <el-card shadow="never">
      <el-tabs v-model="role" @tab-change="changeRole">
        <el-tab-pane label="普通用户" name="regular" />
        <el-tab-pane label="超管用户" name="superadmin" />
      </el-tabs>

      <el-table :data="users" v-loading="loading" row-key="id">
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column prop="username" label="用户名" min-width="180" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '正常' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" min-width="190">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column v-if="role === 'regular'" label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button
              text
              :type="row.is_active ? 'danger' : 'primary'"
              :loading="pendingUserId === row.id"
              @click="toggleStatus(row)"
            >{{ row.is_active ? '停用' : '启用' }}</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无用户" />
        </template>
      </el-table>

      <div class="mt-5 flex justify-end">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadUsers"
        />
      </div>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsersApi, updateUserStatusApi, type ManagedUser, type UserRole } from '@/api/users'

const role = ref<UserRole>('regular')
const users = ref<ManagedUser[]>([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)
const pendingUserId = ref<number | null>(null)

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleString() : '-'
}

async function loadUsers() {
  loading.value = true
  try {
    const result = await getUsersApi(role.value, page.value, pageSize)
    users.value = result.items
    total.value = result.total
  } catch {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

function changeRole() {
  page.value = 1
  void loadUsers()
}

async function toggleStatus(user: ManagedUser) {
  const isActive = !user.is_active
  if (!isActive) {
    try {
      await ElMessageBox.confirm(`确定停用用户“${user.username}”吗？该用户将无法继续使用账号。`, '停用用户', { type: 'warning' })
    } catch {
      return
    }
  }
  pendingUserId.value = user.id
  try {
    const result = await updateUserStatusApi(user.id, isActive)
    user.is_active = result.is_active
    ElMessage.success(isActive ? '用户已启用' : '用户已停用')
  } catch {
    ElMessage.error('更新用户状态失败')
  } finally {
    pendingUserId.value = null
  }
}

onMounted(loadUsers)
</script>
