<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { Plus, RefreshCcw } from 'lucide-vue-next'

import { makeupApi, studentApi } from '../api/modules'
import DataTable from '../components/DataTable.vue'
import EmptyState from '../components/EmptyState.vue'
import MessageBar from '../components/MessageBar.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { makeupStatuses, subjects } from '../constants/options'

const makeups = ref([])
const failedExams = ref([])
const loading = ref(false)
const saving = ref(false)
const loadingExams = ref(false)
const message = reactive({ text: '', type: 'info' })
const form = reactive({
  studentName: '',
  idNumber: '',
  originalSubject: '科目二',
  failedScore: 0,
  scheduledDate: '',
  notes: '',
  sourceExamId: null
})

const columns = [
  { key: 'studentName', label: '学员' },
  { key: 'idNumber', label: '证件号' },
  { key: 'originalSubject', label: '原科目' },
  { key: 'failedScore', label: '失败分数' },
  { key: 'scheduledDate', label: '补考日期' },
  { key: 'status', label: '状态' },
  { key: 'notes', label: '备注' },
  { key: 'sourceExamId', label: '关联考试' }
]

async function loadFailedExams() {
  if (!form.studentName && !form.idNumber) {
    failedExams.value = []
    form.sourceExamId = null
    return
  }
  loadingExams.value = true
  try {
    const params = {}
    if (form.idNumber) params.idNumber = form.idNumber
    if (form.studentName) params.studentName = form.studentName
    failedExams.value = await studentApi.getFailedExams(params)
    const currentId = form.sourceExamId
    if (currentId && !failedExams.value.some(e => e.id === currentId)) {
      form.sourceExamId = null
    }
  } catch (error) {
    failedExams.value = []
    form.sourceExamId = null
  } finally {
    loadingExams.value = false
  }
}

watch(
  () => [form.studentName, form.idNumber],
  () => {
    loadFailedExams()
  },
  { debounce: 300 }
)

async function loadMakeups() {
  loading.value = true
  try {
    makeups.value = await makeupApi.list()
  } catch (error) {
    message.text = error.message
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

async function createMakeup() {
  saving.value = true
  message.text = ''
  try {
    const payload = { ...form }
    if (!payload.sourceExamId) delete payload.sourceExamId
    await makeupApi.create(payload)
    Object.assign(form, {
      studentName: '',
      idNumber: '',
      originalSubject: form.originalSubject,
      failedScore: 0,
      scheduledDate: '',
      notes: '',
      sourceExamId: null
    })
    failedExams.value = []
    message.text = '补考记录已创建'
    message.type = 'success'
    await loadMakeups()
  } catch (error) {
    message.text = error.message
    message.type = 'error'
  } finally {
    saving.value = false
  }
}

async function updateMakeup(row, payload) {
  try {
    const isCancelling = payload.status === '已取消' && row.status !== '已取消'
    const hasLinkedExam = isCancelling && row.sourceExamId

    if (hasLinkedExam) {
      const confirmed = window.confirm(
        `确定要取消这次补考吗？\n\n取消后将释放关联的考试 #${row.sourceExamId}，` +
        `该考试会重新出现在"可关联考试"列表中，可以再次选择关联。`
      )
      if (!confirmed) {
        return
      }
    }

    await makeupApi.update(row.id, payload)
    await loadMakeups()

    if (hasLinkedExam) {
      message.text = `补考已取消，已释放关联考试 #${row.sourceExamId}，可重新选择关联`
      message.type = 'success'
      if (form.studentName || form.idNumber) {
        await loadFailedExams()
      }
    }
  } catch (error) {
    message.text = error.message
    message.type = 'error'
  }
}

onMounted(loadMakeups)
</script>

<template>
  <section class="module-grid two-columns">
    <form class="panel form-panel" @submit.prevent="createMakeup">
      <div class="panel-heading">
        <div>
          <h3>新增补考</h3>
          <p>模拟考试未通过会自动生成，也可手动登记。</p>
        </div>
        <Plus :size="20" />
      </div>

      <MessageBar :message="message.text" :type="message.type" />

      <label>
        <span>学员姓名</span>
        <input v-model.trim="form.studentName" required placeholder="请输入姓名" />
      </label>
      <label>
        <span>证件号</span>
        <input v-model.trim="form.idNumber" placeholder="身份证或档案号（用于轨迹查询）" />
      </label>
      <div class="field-row">
        <label>
          <span>原科目</span>
          <select v-model="form.originalSubject">
            <option v-for="subject in subjects" :key="subject">{{ subject }}</option>
          </select>
        </label>
        <label>
          <span>失败分数</span>
          <input v-model.number="form.failedScore" min="0" max="100" type="number" />
        </label>
      </div>
      <label>
        <span>补考日期</span>
        <input v-model="form.scheduledDate" type="date" />
      </label>
      <label>
        <span>关联考试</span>
        <select
          v-model="form.sourceExamId"
          :disabled="loadingExams || failedExams.length === 0"
        >
          <option :value="null">
            {{ loadingExams ? '加载中...' : (failedExams.length === 0 ? '请先输入学员信息' : '不关联（独立补考）') }}
          </option>
          <option
            v-for="exam in failedExams"
            :key="exam.id"
            :value="exam.id"
          >
            {{ exam.description }}
          </option>
        </select>
        <p v-if="form.sourceExamId && form.studentName" class="field-hint">
          登记后该补考将在考试轨迹中与所选考试关联显示
        </p>
      </label>
      <label>
        <span>备注</span>
        <textarea v-model.trim="form.notes" rows="3" placeholder="训练重点或失败原因"></textarea>
      </label>

      <button class="primary-button" :disabled="saving" type="submit">
        <Plus :size="18" />
        <span>{{ saving ? '保存中' : '登记补考' }}</span>
      </button>
    </form>

    <section class="panel list-panel">
      <div class="panel-heading">
        <div>
          <h3>补考列表</h3>
          <p>安排补考日期并跟踪处理状态。</p>
        </div>
        <button class="icon-button" type="button" title="刷新" @click="loadMakeups">
          <RefreshCcw :size="18" />
        </button>
      </div>

      <EmptyState v-if="!loading && makeups.length === 0" title="暂无补考" description="补考记录将在这里显示。" />
      <DataTable v-else :columns="columns" :rows="makeups">
        <template #status="{ row }">
          <StatusBadge :status="row.status" />
        </template>
        <template #sourceExamId="{ row }">
          <span v-if="row.sourceExamId" class="link-badge">
            关联考试 #{{ row.sourceExamId }}
          </span>
          <span v-else class="muted-text">-</span>
        </template>
        <template #scheduledDate="{ row }">
          <input
            class="table-input"
            type="date"
            :value="row.scheduledDate || ''"
            @change="updateMakeup(row, { scheduledDate: $event.target.value, status: row.status === '待安排' ? '已安排' : row.status })"
          />
        </template>
        <template #actions="{ row }">
          <select class="compact-select" :value="row.status" @change="updateMakeup(row, { status: $event.target.value })">
            <option v-for="status in makeupStatuses" :key="status">{{ status }}</option>
          </select>
        </template>
      </DataTable>
    </section>
  </section>
</template>
