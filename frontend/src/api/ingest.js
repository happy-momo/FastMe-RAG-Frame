import http from './http'

// Scenes
export function fetchScenes() {
  return http.get('/api/scenes')
}

// Sessions
export function fetchSessions() {
  return http.get('/api/sessions')
}
export function createSession(id) {
  return http.post('/api/sessions', { id })
}
export function deleteSession(id) {
  return http.delete(`/api/sessions/${encodeURIComponent(id)}`)
}
export function fetchSessionMessages(sessionId) {
  return http.get(`/api/sessions/${encodeURIComponent(sessionId)}/messages`)
}

// Ingest (multipart upload)
export function uploadDocument(file, docType, extraMetadata) {
  const form = new FormData()
  form.append('file', file)
  form.append('doc_type', docType)
  if (extraMetadata) form.append('extra_metadata', JSON.stringify(extraMetadata))
  return http.post('/api/ingest', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// Health
export function fetchHealth() {
  return http.get('/healthz')
}