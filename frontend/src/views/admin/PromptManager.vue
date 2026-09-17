<script setup lang="ts">
/**
 * views/admin/PromptManager.vue
 * Prompt 模板管理：CRUD + 版本管理 + 一键启用
 */
import { ref, onMounted } from 'vue';
import {
  listPrompts,
  createPrompt,
  updatePrompt,
  deletePrompt,
  type PromptItem,
} from '@/api/admin';
import { ElMessage, ElMessageBox } from 'element-plus';

const list = ref<PromptItem[]>([]);
const loading = ref(false);
const dialogOpen = ref(false);
const editing = ref<Partial<PromptItem> | null>(null);

async function load() {
  loading.value = true;
  try {
    list.value = await listPrompts();
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

function openNew() {
  editing.value = { type: 'travel', name: '', content: '', enabled: true, version: 1 };
  dialogOpen.value = true;
}

function openEdit(item: PromptItem) {
  editing.value = { ...item };
  dialogOpen.value = true;
}

async function handleSave() {
  if (!editing.value?.name || !editing.value.content) {
    ElMessage.warning('请填写名称和内容');
    return;
  }
  try {
    if (editing.value.id) {
      await updatePrompt(editing.value.id, editing.value);
      ElMessage.success('已更新');
    } else {
      await createPrompt(editing.value);
      ElMessage.success('已创建');
    }
    dialogOpen.value = false;
    await load();
  } catch (e) {
    console.error(e);
  }
}

async function handleToggle(item: PromptItem) {
  try {
    await updatePrompt(item.id, { enabled: !item.enabled });
    ElMessage.success(item.enabled ? '已停用' : '已启用');
    await load();
  } catch (e) {
    console.error(e);
  }
}

async function handleDelete(item: PromptItem) {
  try {
    await ElMessageBox.confirm(`确认删除「${item.name}」？`, '提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    });
    await deletePrompt(item.id);
    ElMessage.success('已删除');
    await load();
  } catch (e) {
    /* cancel */
  }
}

onMounted(load);
</script>

<template>
  <div class="prompt-manager">
    <header class="page-header">
      <h1 class="page-title">Prompt 模板</h1>
      <p class="page-desc">管理各业务场景的 AI Prompt 模板</p>
    </header>

    <div class="toolbar">
      <button class="action-btn primary" @click="openNew">
        <el-icon :size="18"><Plus /></el-icon>
        <span>新建模板</span>
      </button>
    </div>

    <div v-if="loading" class="loading" aria-busy="true">加载中…</div>
    <el-table v-else :data="list" stripe>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="version" label="版本" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'">
            {{ row.enabled ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updatedAt" label="更新时间" width="180" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <button class="row-btn" @click="openEdit(row)">编辑</button>
          <button class="row-btn" @click="handleToggle(row)">
            {{ row.enabled ? '停用' : '启用' }}
          </button>
          <button class="row-btn danger" @click="handleDelete(row)">删除</button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogOpen" :title="editing?.id ? '编辑模板' : '新建模板'" width="640px">
      <div v-if="editing" class="form-grid">
        <div class="form-row">
          <label class="form-label">名称</label>
          <el-input v-model="editing.name" />
        </div>
        <div class="form-row">
          <label class="form-label">类型</label>
          <el-select v-model="editing.type" style="width: 100%;">
            <el-option label="出行" value="travel" />
            <el-option label="OCR" value="ocr" />
            <el-option label="货币" value="currency" />
            <el-option label="商品" value="product" />
            <el-option label="人脸" value="face" />
          </el-select>
        </div>
        <div class="form-row">
          <label class="form-label">Prompt 内容</label>
          <el-input
            v-model="editing.content"
            type="textarea"
            :rows="8"
            placeholder="请输入 Prompt 模板内容"
          />
        </div>
        <div class="form-row inline">
          <label class="form-label">启用</label>
          <el-switch v-model="editing.enabled" />
        </div>
      </div>
      <template #footer>
        <button class="dialog-btn" @click="dialogOpen = false">取消</button>
        <button class="dialog-btn primary" @click="handleSave">保存</button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.prompt-manager { display: flex; flex-direction: column; gap: 20px; }
.page-header { text-align: center; }
.page-title { font-size: 24px; color: $text-main; margin: 0 0 4px; }
.page-desc { color: $text-secondary; font-size: 14px; margin: 0; }
.toolbar { display: flex; justify-content: flex-end; }
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 44px;
  padding: 0 20px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  color: $text-main;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  &.primary {
    background: $accent;
    color: #fff;
  }
  &:hover { box-shadow: $shadow-md; }
  &:focus-visible { outline: 2px solid $accent; outline-offset: 2px; }
}
.loading { text-align: center; padding: 24px; color: $text-secondary; }
.row-btn {
  height: 32px;
  padding: 0 12px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-sm;
  color: $text-main;
  cursor: pointer;
  font-size: 13px;
  margin-right: 4px;
  &:hover { background: $bg-elevated; }
  &.danger { color: $color-danger; }
  &:focus-visible { outline: 2px solid $accent; }
}
.form-grid { display: flex; flex-direction: column; gap: 16px; }
.form-row { display: flex; flex-direction: column; gap: 6px; }
.form-row.inline { flex-direction: row; align-items: center; }
.form-label { font-size: 14px; color: $text-main; font-weight: 500; }
.dialog-btn {
  height: 40px;
  padding: 0 18px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  color: $text-main;
  cursor: pointer;
  margin-left: 8px;
  &.primary { background: $accent; color: #fff; }
  &:focus-visible { outline: 2px solid $accent; outline-offset: 2px; }
}
</style>
