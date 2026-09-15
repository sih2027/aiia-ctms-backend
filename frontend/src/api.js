import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aayur_sathi_token') || localStorage.getItem('aiia_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('aayur_sathi_token');
        localStorage.removeItem('aiia_token');
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
  investigators: () => api.get('/auth/investigators'),
};

export const studiesApi = {
  list: () => api.get('/studies'),
  get: (id) => api.get(`/studies/${id}`),
  create: (data) => api.post('/studies', data),
  iecDecision: (id, data) => api.post(`/studies/${id}/iec-decision`, data),
  ctriRegister: (id, data) => api.post(`/studies/${id}/ctri-register`, data),
  getTeam: (id) => api.get(`/studies/${id}/team`),
  assignTeam: (id, data) => api.post(`/studies/${id}/team`, data),
  removeTeam: (id, userId) => api.delete(`/studies/${id}/team/${userId}`),
};

export const patientsApi = {
  listForStudy: (studyId) => api.get(`/patients/study/${studyId}`),
  get: (id) => api.get(`/patients/${id}`),
  screen: (data) => api.post('/patients/screen', data),
  enroll: (data) => api.post('/patients/enroll', data),
  getConsent: (patientId) => api.get(`/patients/${patientId}/consent`),
  recordConsent: (patientId, data) => api.post(`/patients/${patientId}/consent`, data),
  withdrawConsent: (patientId, data) => api.post(`/patients/${patientId}/withdraw-consent`, data),
  getVisits: (patientId) => api.get(`/patients/${patientId}/visits`),
  createVisit: (data) => api.post('/patients/visits', data),
  updateVisit: (visitId, data) => api.put(`/patients/visits/${visitId}`, data),
  getDeviations: (studyId) => api.get(`/patients/study/${studyId}/deviations`),
  createDeviation: (data) => api.post('/patients/deviations', data),
  getIECriteria: (studyId) => api.get(`/patients/studies/${studyId}/ie-criteria`),
  createIECriteria: (studyId, data) => api.post(`/patients/studies/${studyId}/ie-criteria`, data),
  getIEResults: (patientId) => api.get(`/patients/${patientId}/ie-results`),
  recordIEResult: (patientId, data) => api.post(`/patients/${patientId}/ie-results`, data),
};

export const aeApi = {
  list: (params) => api.get('/ae', { params }),
  get: (id) => api.get(`/ae/${id}`),
  create: (data) => api.post('/ae', data),
  updateStatus: (id, data) => api.put(`/ae/${id}/status`, data),
  summary: (studyId) => api.get(`/ae/summary/${studyId}`),
  dsmbFeed: () => api.get('/ae/dsmb/feed'),
  terms: () => api.get('/ae/terms'),
  signals: () => api.get('/ae/signals'),
  overdue: () => api.get('/ae/overdue'),
  assessCausality: (id, data) => api.patch(`/ae/${id}/causality`, data),
};

export const queriesApi = {
  list: (params) => api.get('/queries', { params }),
  create: (data) => api.post('/queries', data),
  answer: (id, data) => api.patch(`/queries/${id}/answer`, data),
  close: (id, data) => api.patch(`/queries/${id}/close`, data),
};

export const monitoringApi = {
  list: (params) => api.get('/monitoring-visits', { params }),
  create: (data) => api.post('/monitoring-visits', data),
};

export const notificationsApi = {
  list: () => api.get('/notifications'),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
  readAll: () => api.post('/notifications/read-all'),
};

export const abdmApi = {
  verify: (abhaId) => api.post('/abdm/verify-health-id', { abha_id: abhaId }),
  pushCareContext: (data) => api.post('/abdm/push-care-context', data),
};

export const auditApi = {
  trail: (params) => api.get('/audit/trail', { params }),
  verify: (simulateTamper = false) => api.get('/audit/verify', { params: { simulate_tamper: simulateTamper } }),
  anchor: () => api.post('/audit/anchor'),
  simulateTamper: () => api.post('/audit/simulate-tamper'),
  restoreTamper: () => api.post('/audit/restore-tamper'),
};

export const fhirApi = {
  study: (studyId) => api.get(`/fhir/ResearchStudy/${studyId}`),
  ae: (aeId) => api.get(`/fhir/AdverseEvent/${aeId}`),
  patient: (patientId) => api.get(`/fhir/Patient/${patientId}`),
};

export const exportApi = {
  dmUrl: (studyId) => `${API_BASE}/export/sdtm/dm/${studyId}`,
  aeUrl: (studyId) => `${API_BASE}/export/sdtm/ae/${studyId}`,
  ieUrl: (studyId) => `${API_BASE}/export/sdtm/ie/${studyId}`,
  defineUrl: (studyId) => `${API_BASE}/export/sdtm/define/${studyId}`,
};
