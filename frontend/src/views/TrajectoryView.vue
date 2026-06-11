<script setup>
import { computed, reactive, ref } from 'vue'
import { ArrowRight, CalendarCheck, ClipboardList, Link2, RotateCcw, Search, User } from 'lucide-vue-next'

import { studentApi } from '../api/modules'
import EmptyState from '../components/EmptyState.vue'
import MessageBar from '../components/MessageBar.vue'
import StatusBadge from '../components/StatusBadge.vue'

const loading = ref(false)
const message = reactive({ text: '', type: 'info' })
const filters = reactive({ idNumber: '', studentName: '' })

const trajectory = ref(null)

function setMessage(text, type = 'info') {
  message.text = text
  message.type = type
}

async function searchTrajectory() {
  if (!filters.idNumber.trim() && !filters.studentName.trim()) {
    setMessage('请输入证件号或学员姓名', 'error')
    return
  }
  loading.value = true
  setMessage('')
  try {
    const params = {}
    if (filters.idNumber.trim()) params.idNumber = filters.idNumber.trim()
    if (filters.studentName.trim()) params.studentName = filters.studentName.trim()
    trajectory.value = await studentApi.trajectory(params)
    if (!trajectory.value || trajectory.value.timeline.length === 0) {
      setMessage('未查询到该学员的考试轨迹', 'info')
    }
  } catch (error) {
    trajectory.value = null
    setMessage(error.message, 'error')
  } finally {
    loading.value = false
  }
}

function getTypeIcon(type) {
  switch (type) {
    case 'appointment':
      return CalendarCheck
    case 'exam':
      return ClipboardList
    case 'makeup':
      return RotateCcw
    default:
      return CalendarCheck
  }
}

function getTypeLabel(type) {
  switch (type) {
    case 'appointment':
      return '预约'
    case 'exam':
      return '考试'
    case 'makeup':
      return '补考'
    default:
      return '记录'
  }
}

function getTypeClass(type) {
  return `timeline-type timeline-type-${type}`
}

function isLastInGroup(index, list) {
  const current = list[index]
  const next = list[index + 1]
  if (!current.groupId) return true
  if (!next) return true
  return current.groupId !== next.groupId
}

function isFirstInGroup(index, list) {
  const current = list[index]
  const prev = list[index - 1]
  if (!current.groupId) return true
  if (!prev) return true
  return current.groupId !== prev.groupId
}
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <div>
        <h3>学员考试轨迹</h3>
        <p>按学员姓名或证件号查询完整考试轨迹，串联预约、成绩与补考记录。</p>
      </div>
    </div>

    <form class="toolbar trajectory-toolbar" @submit.prevent="searchTrajectory">
      <label>
        <span>证件号</span>
        <input v-model.trim="filters.idNumber" placeholder="身份证或档案号" />
      </label>
      <label>
        <span>学员姓名</span>
        <input v-model.trim="filters.studentName" placeholder="输入学员姓名" />
      </label>
      <button class="primary-button inline-button" type="submit" :disabled="loading">
        <Search :size="18" />
        <span>{{ loading ? '查询中' : '查询轨迹' }}</span>
      </button>
    </form>

    <MessageBar :message="message.text" :type="message.type" />

    <EmptyState
      v-if="!loading && !trajectory"
      title="请先查询学员"
      description="输入学员证件号或姓名后点击查询，即可查看完整考试轨迹。"
    />

    <template v-else-if="trajectory">
      <section class="trajectory-header">
        <div class="student-info">
          <div class="student-avatar">
            <User :size="28" />
          </div>
          <div>
            <h4 class="student-name">
              {{ trajectory.student.studentName || '未知学员' }}
            </h4>
            <p class="student-id">
              证件号：{{ trajectory.student.idNumber || '未记录' }}
            </p>
          </div>
        </div>
        <div class="summary-grid">
          <div class="summary-card">
            <span class="summary-label">预约次数</span>
            <span class="summary-value">{{ trajectory.summary.totalAppointments }}</span>
          </div>
          <div class="summary-card">
            <span class="summary-label">考试次数</span>
            <span class="summary-value">{{ trajectory.summary.totalExams }}</span>
          </div>
          <div class="summary-card summary-pass">
            <span class="summary-label">通过次数</span>
            <span class="summary-value">{{ trajectory.summary.passedExams }}</span>
          </div>
          <div class="summary-card summary-fail">
            <span class="summary-label">未通过</span>
            <span class="summary-value">{{ trajectory.summary.failedExams }}</span>
          </div>
          <div class="summary-card summary-makeup">
            <span class="summary-label">补考次数</span>
            <span class="summary-value">{{ trajectory.summary.totalMakeups }}</span>
          </div>
          <div class="summary-card summary-pending">
            <span class="summary-label">待处理补考</span>
            <span class="summary-value">{{ trajectory.summary.pendingMakeups }}</span>
          </div>
        </div>
      </section>

      <div class="timeline-wrapper">
        <div class="timeline-title">
          <h4>考试轨迹时间线</h4>
          <span>共 {{ trajectory.timeline.length }} 条记录</span>
        </div>

        <EmptyState
          v-if="trajectory.timeline.length === 0"
          title="暂无轨迹记录"
          description="该学员尚未产生预约、考试或补考记录。"
        />

        <ul v-else class="timeline-list">
          <template
            v-for="(item, index) in trajectory.timeline"
            :key="`${item.type}-${item.id}-${index}`"
          >
            <li
              v-if="item.groupRole === 'head'"
              class="timeline-item grouped grouped-head"
            >
              <div class="timeline-node">
                <div class="timeline-icon" :class="getTypeClass(item.type)">
                  <component :is="getTypeIcon(item.type)" :size="16" />
                </div>
                <div
                  v-if="index < trajectory.timeline.length - 1"
                  class="timeline-line linked-line"
                />
              </div>
              <div class="timeline-content grouped-head-content linked-content">
                <div class="timeline-head">
                  <span class="timeline-type-tag" :class="getTypeClass(item.type)">
                    {{ getTypeLabel(item.type) }}
                  </span>
                  <h5 class="timeline-item-title">{{ item.title }}</h5>
                  <StatusBadge :status="item.status" />
                </div>
                <p class="timeline-desc">{{ item.description }}</p>
                <p class="timeline-time">{{ item.datetime.replace('T', ' ') }}</p>

                <div class="linked-makeup-indicator">
                  <Link2 :size="14" />
                  <span>本次考试未通过，已生成补考记录：</span>
                </div>
              </div>
            </li>

            <li
              v-else-if="item.groupRole === 'tail'"
              class="timeline-item grouped grouped-tail"
            >
              <div class="timeline-node">
                <div class="timeline-icon makeup-linked-icon">
                  <ArrowRight :size="14" />
                </div>
                <div
                  v-if="!isLastInGroup(index, trajectory.timeline)"
                  class="timeline-line"
                />
              </div>
              <div class="timeline-content grouped-tail-content linked-content">
                <div class="timeline-head">
                  <span class="timeline-type-tag timeline-type-makeup linked-tag">
                    {{ getTypeLabel(item.type) }}
                  </span>
                  <h5 class="timeline-item-title">{{ item.title }}</h5>
                  <StatusBadge :status="item.status" />
                </div>
                <p class="timeline-desc">{{ item.description }}</p>
                <p class="timeline-time">{{ item.datetime.replace('T', ' ') }}</p>
              </div>
            </li>

            <li
              v-else
              class="timeline-item ungrouped"
            >
              <div class="timeline-node">
                <div class="timeline-icon" :class="getTypeClass(item.type)">
                  <component :is="getTypeIcon(item.type)" :size="16" />
                </div>
                <div
                  v-if="index < trajectory.timeline.length - 1"
                  class="timeline-line"
                />
              </div>
              <div class="timeline-content">
                <div class="timeline-head">
                  <span class="timeline-type-tag" :class="getTypeClass(item.type)">
                    {{ getTypeLabel(item.type) }}
                  </span>
                  <h5 class="timeline-item-title">{{ item.title }}</h5>
                  <StatusBadge :status="item.status" />
                </div>
                <p class="timeline-desc">{{ item.description }}</p>
                <p class="timeline-time">{{ item.datetime.replace('T', ' ') }}</p>
              </div>
            </li>
          </template>
        </ul>
      </div>
    </template>
  </section>
</template>

<style scoped>
.trajectory-toolbar {
  grid-template-columns: 1fr 1fr auto;
}

.trajectory-header {
  display: grid;
  gap: 20px;
  margin-bottom: 24px;
  padding: 18px;
  border: 1px solid #e5ebef;
  border-radius: 8px;
  background: #f9fbfc;
}

.student-info {
  display: flex;
  gap: 14px;
  align-items: center;
}

.student-avatar {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #1f7a8c;
  color: #fff;
}

.student-name {
  margin: 0;
  font-size: 18px;
  color: #111827;
}

.student-id {
  margin: 4px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  display: grid;
  gap: 4px;
  padding: 14px 12px;
  border: 1px solid #e5ebef;
  border-radius: 8px;
  background: #fff;
  text-align: center;
}

.summary-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 600;
}

.summary-value {
  font-size: 24px;
  font-weight: 900;
  color: #1f7a8c;
}

.summary-pass .summary-value {
  color: #1e6b3f;
}

.summary-fail .summary-value {
  color: #a32929;
}

.summary-makeup .summary-value {
  color: #8a5a00;
}

.summary-pending .summary-value {
  color: #7c3aed;
}

.timeline-wrapper {
  margin-top: 8px;
}

.timeline-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.timeline-title h4 {
  margin: 0;
  font-size: 15px;
  color: #1f2937;
}

.timeline-title span {
  font-size: 12px;
  color: #6b7280;
}

.timeline-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0;
}

.timeline-item {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  gap: 14px;
}

.timeline-item.grouped.grouped-head + .timeline-item.grouped.grouped-tail {
  margin-top: 4px;
}

.timeline-item.ungrouped {
  margin-bottom: 4px;
}

.timeline-node {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 6px;
}

.timeline-icon {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #e5ebef;
  color: #425466;
  z-index: 1;
  flex-shrink: 0;
}

.timeline-icon.makeup-linked-icon {
  width: 22px;
  height: 22px;
  margin-top: 4px;
  background: linear-gradient(135deg, #fef3c7, #f59e0b);
  color: #78350f;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px #f59e0b, 0 2px 6px rgba(245, 158, 11, 0.3);
}

.timeline-line {
  flex: 1;
  width: 2px;
  min-height: 28px;
  background: #e5ebef;
  margin-top: 4px;
}

.timeline-line.linked-line {
  background: linear-gradient(180deg, #10b981 0%, #f59e0b 100%);
  width: 3px;
  min-height: 16px;
}

.timeline-type-appointment {
  background: #dbeafe;
  color: #1d4ed8;
}

.timeline-type-exam {
  background: #d1fae5;
  color: #065f46;
}

.timeline-type-makeup {
  background: #fef3c7;
  color: #92400e;
}

.timeline-content {
  border: 1px solid #e5ebef;
  border-radius: 8px;
  padding: 14px 16px;
  background: #fff;
}

.timeline-content.linked-content {
  border-style: dashed;
  border-width: 2px;
}

.timeline-item.grouped-head .grouped-head-content {
  background: linear-gradient(180deg, #fff 0%, #fefce8 100%);
  border-color: #f59e0b;
  border-width: 2px;
  border-style: solid;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-bottom: 1px dashed #f59e0b;
}

.timeline-item.grouped-tail .grouped-tail-content {
  background: linear-gradient(180deg, #fffbeb 0%, #fff 100%);
  border-color: #f59e0b;
  border-width: 2px;
  border-style: solid;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  border-top: none;
  margin-bottom: 8px;
}

.timeline-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.timeline-type-tag {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.timeline-type-tag.timeline-type-appointment {
  background: #dbeafe;
  color: #1d4ed8;
}

.timeline-type-tag.timeline-type-exam {
  background: #d1fae5;
  color: #065f46;
}

.timeline-type-tag.timeline-type-makeup {
  background: #fef3c7;
  color: #92400e;
}

.timeline-type-tag.linked-tag {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff;
}

.timeline-item-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #111827;
  flex: 1;
}

.timeline-desc {
  margin: 8px 0 4px;
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
}

.timeline-time {
  margin: 0;
  font-size: 12px;
  color: #9ca3af;
}

.linked-makeup-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 6px 10px;
  background: #fffbeb;
  border: 1px dashed #f59e0b;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #92400e;
}

@media (max-width: 980px) {
  .trajectory-toolbar {
    grid-template-columns: 1fr;
  }

  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
