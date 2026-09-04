import http from './http'

// 同步对话 / synchronous chat
export function sendChat(payload) {
  return http.post('/api/chat', payload)
}

// 流式对话：使用 fetch + ReadableStream 解析 SSE，返回一个 AsyncGenerator
// Streaming chat: parse SSE via fetch + ReadableStream, returns an AsyncGenerator
export async function* streamChat(payload, onEvent) {
  const resp = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!resp.ok || !resp.body) {
    let msg = `流式请求失败：HTTP ${resp.status}`
    let detail = ''
    try {
      detail = (await resp.json())?.detail || ''
    } catch (e) {
      /* ignore */
    }
    throw new Error(detail || msg)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE 帧以空行分隔 / frames separated by blank line
    let idx
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const rawFrame = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)

      let event = 'message'
      let data = ''
      for (const line of rawFrame.split('\n')) {
        if (line.startsWith('event: ')) event = line.slice(7)
        else if (line.startsWith('data: ')) data += line.slice(6)
      }
      if (!data) continue

      let parsed = data
      try {
        parsed = JSON.parse(data)
      } catch (e) {
        /* keep raw text */
      }
      onEvent?.(event, parsed)
      yield { event, data: parsed }
    }
  }
}