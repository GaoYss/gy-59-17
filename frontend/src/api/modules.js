import { api } from './http'

export const appointmentApi = {
  list: () => api.get('/api/appointments'),
  create: (payload) => api.post('/api/appointments', payload),
  updateStatus: (id, status) => api.patch(`/api/appointments/${id}`, { status })
}

export const examApi = {
  questions: (subject) => api.get(`/api/exams/questions?subject=${encodeURIComponent(subject)}`),
  submit: (payload) => api.post('/api/exams/submit', payload)
}

export const scoreApi = {
  list: (params = {}) => {
    const query = new URLSearchParams(params)
    const suffix = query.toString() ? `?${query}` : ''
    return api.get(`/api/scores${suffix}`)
  }
}

export const makeupApi = {
  list: () => api.get('/api/makeups'),
  create: (payload) => api.post('/api/makeups', payload),
  update: (id, payload) => api.patch(`/api/makeups/${id}`, payload)
}

export const ruleApi = {
  list: () => api.get('/api/rules'),
  update: (id, payload) => api.patch(`/api/rules/${id}`, payload)
}

export const studentApi = {
  trajectory: (params = {}) => {
    const query = new URLSearchParams()
    if (params.idNumber) query.set('idNumber', params.idNumber)
    if (params.studentName) query.set('studentName', params.studentName)
    const suffix = query.toString() ? `?${query}` : ''
    return api.get(`/api/students/trajectory${suffix}`)
  },
  getFailedExams: (params = {}) => {
    const query = new URLSearchParams()
    if (params.idNumber) query.set('idNumber', params.idNumber)
    if (params.studentName) query.set('studentName', params.studentName)
    const suffix = query.toString() ? `?${query}` : ''
    return api.get(`/api/students/failed-exams${suffix}`)
  }
}
