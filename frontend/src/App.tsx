import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react'
import './App.css'

// ─── Types ──────────────────────────────────────────────────────
type ThinkingMode = 'auto' | 'on' | 'off'

interface LawInfo {
  id: string
  label: string
}

interface RefinedInfo {
  original: string
  intent: string | null
  objective: string
  refined: string
}

interface ChatContext {
  vector_context?: string | null
  graph_context?: string | null
  graph_article_ids?: string[] | null
}

interface AssistantMessage {
  role: 'assistant'
  answer: string
  thinking: string
  refined: RefinedInfo | null
  intent: string
  thinking_used: boolean
  context?: ChatContext
  streaming?: boolean
}

interface UserMessage {
  role: 'user'
  text: string
}

interface ErrorMessage {
  role: 'error'
  text: string
}

type Message = UserMessage | AssistantMessage | ErrorMessage

interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: number
}

// ─── Helpers ────────────────────────────────────────────────────
const SUGGESTIONS = [
  'Điều 15 Luật An ninh mạng 2025 quy định gì?',
  'Phân biệt lỗ hổng bảo mật và sự cố an ninh mạng theo Luật.',
  'Doanh nghiệp viễn thông có nghĩa vụ gì khi đại lý đăng ký SIM sai thông tin?',
  'So sánh Luật CNTT 2006 và Luật CNTT 2025 về điều kiện kinh doanh.',
]

function genId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`
}

function newConversation(): Conversation {
  return {
    id: genId(),
    title: 'New chat',
    messages: [],
    createdAt: Date.now(),
  }
}

function truncate(s: string, n: number): string {
  const t = s.trim().replace(/\s+/g, ' ')
  return t.length <= n ? t : t.slice(0, n - 1) + '…'
}

// ─── App ────────────────────────────────────────────────────────
export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(() => [
    newConversation(),
  ])
  const [activeId, setActiveId] = useState<string>(() => conversations[0].id)

  const [laws, setLaws] = useState<LawInfo[]>([])
  const [lawId, setLawId] = useState<string>('')
  const [thinking, setThinking] = useState<ThinkingMode>('auto')
  const [showContext, setShowContext] = useState<boolean>(false)

  const [input, setInput] = useState<string>('')
  const [sending, setSending] = useState<boolean>(false)

  const chatRef = useRef<HTMLDivElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  const active = useMemo(
    () => conversations.find((c) => c.id === activeId) ?? conversations[0],
    [conversations, activeId],
  )

  // Load laws once
  useEffect(() => {
    fetch('/api/laws')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((data: LawInfo[]) => setLaws(data))
      .catch(() => {
        /* leave empty — UI still works */
      })
  }, [])

  // Auto-scroll chat
  useEffect(() => {
    const el = chatRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [active?.messages, sending])

  // Auto-grow textarea
  useEffect(() => {
    const t = textareaRef.current
    if (!t) return
    t.style.height = 'auto'
    t.style.height = Math.min(t.scrollHeight, 220) + 'px'
  }, [input])

  // ─── Mutators ────────────────────────────────────────────────
  const updateActive = useCallback(
    (fn: (c: Conversation) => Conversation) => {
      setConversations((cs) => cs.map((c) => (c.id === activeId ? fn(c) : c)))
    },
    [activeId],
  )

  const handleNewChat = () => {
    const c = newConversation()
    setConversations((cs) => [c, ...cs])
    setActiveId(c.id)
    setInput('')
  }

  const handleSelectConv = (id: string) => setActiveId(id)

  const handleDeleteConv = (id: string) => {
    setConversations((cs) => {
      const next = cs.filter((c) => c.id !== id)
      if (next.length === 0) {
        const fresh = newConversation()
        setActiveId(fresh.id)
        return [fresh]
      }
      if (id === activeId) setActiveId(next[0].id)
      return next
    })
  }

  // ─── Send (streaming via SSE) ────────────────────────────────
  const send = async (raw?: string) => {
    const query = (raw ?? input).trim()
    if (!query || sending) return

    setInput('')
    setSending(true)

    const userMsg: UserMessage = { role: 'user', text: query }
    // Push user message + placeholder assistant message (streaming = true)
    const placeholder: AssistantMessage = {
      role: 'assistant',
      answer: '',
      thinking: '',
      refined: null,
      intent: '',
      thinking_used: false,
      streaming: true,
    }
    updateActive((c) => ({
      ...c,
      title: c.messages.length === 0 ? truncate(query, 40) : c.title,
      messages: [...c.messages, userMsg, placeholder],
    }))

    // Helper: patch the last assistant message in the active conversation
    const patchLast = (patch: (m: AssistantMessage) => AssistantMessage) => {
      updateActive((c) => {
        const msgs = c.messages.slice()
        for (let i = msgs.length - 1; i >= 0; i--) {
          const m = msgs[i]
          if (m.role === 'assistant') {
            msgs[i] = patch(m)
            break
          }
        }
        return { ...c, messages: msgs }
      })
    }

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify({
          query,
          law_id: lawId || null,
          thinking_mode: thinking,
          include_context: showContext,
        }),
      })
      if (!res.ok || !res.body) {
        const errText = res.body ? await res.text() : ''
        throw new Error(`HTTP ${res.status}: ${errText.slice(0, 200)}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''
      let serverError: string | null = null

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        // SSE events are delimited by blank lines (\n\n)
        let sep: number
        while ((sep = buffer.indexOf('\n\n')) !== -1) {
          const rawEvent = buffer.slice(0, sep)
          buffer = buffer.slice(sep + 2)
          // each line should start with "data:"
          const lines = rawEvent
            .split('\n')
            .map((l) => l.trim())
            .filter((l) => l.startsWith('data:'))
            .map((l) => l.slice(5).trim())
          if (lines.length === 0) continue
          const dataStr = lines.join('')
          if (!dataStr) continue
          let evt: any
          try {
            evt = JSON.parse(dataStr)
          } catch {
            continue
          }
          if (evt.type === 'meta') {
            patchLast((m) => ({
              ...m,
              refined: evt.refined,
              intent: evt.intent,
              thinking_used: !!evt.thinking_used,
              context: showContext
                ? {
                    vector_context: evt.vector_context,
                    graph_context: evt.graph_context,
                    graph_article_ids: evt.graph_article_ids,
                  }
                : undefined,
            }))
          } else if (evt.type === 'thinking') {
            patchLast((m) => ({ ...m, thinking: m.thinking + (evt.delta ?? '') }))
          } else if (evt.type === 'answer') {
            patchLast((m) => ({ ...m, answer: m.answer + (evt.delta ?? '') }))
          } else if (evt.type === 'done') {
            patchLast((m) => ({
              ...m,
              // Server returns cleaned final strings — overwrite to ensure
              // debug-section stripping is applied.
              answer: typeof evt.answer === 'string' ? evt.answer : m.answer,
              thinking:
                typeof evt.thinking === 'string' ? evt.thinking : m.thinking,
              streaming: false,
            }))
          } else if (evt.type === 'error') {
            serverError = evt.message || 'Unknown error'
          }
        }
      }

      if (serverError) {
        // Replace placeholder with error message
        updateActive((c) => {
          const msgs = c.messages.slice()
          for (let i = msgs.length - 1; i >= 0; i--) {
            if (msgs[i].role === 'assistant') {
              msgs[i] = { role: 'error', text: `Lỗi: ${serverError}` }
              break
            }
          }
          return { ...c, messages: msgs }
        })
      } else {
        // Make sure streaming flag is cleared
        patchLast((m) => ({ ...m, streaming: false }))
      }
    } catch (ex: unknown) {
      const msg = ex instanceof Error ? ex.message : String(ex)
      updateActive((c) => {
        const msgs = c.messages.slice()
        for (let i = msgs.length - 1; i >= 0; i--) {
          if (msgs[i].role === 'assistant') {
            msgs[i] = { role: 'error', text: `Lỗi: ${msg}` }
            break
          }
        }
        return { ...c, messages: msgs }
      })
    } finally {
      setSending(false)
    }
  }

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  // ─── Render ─────────────────────────────────────────────────
  const messages = active?.messages ?? []
  const isEmpty = messages.length === 0

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">L</div>
          <div className="sidebar-title">Legal Chat</div>
        </div>

        <button className="new-chat-btn" onClick={handleNewChat}>
          <span>+</span>
          <span>Cuộc trò chuyện mới</span>
        </button>

        <div className="conv-section-title">Lịch sử</div>
        <div className="conv-list">
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`conv-item ${c.id === activeId ? 'active' : ''}`}
              onClick={() => handleSelectConv(c.id)}
            >
              <div className="conv-item-title">{c.title}</div>
              <button
                className="conv-item-del"
                title="Xoá"
                onClick={(e) => {
                  e.stopPropagation()
                  handleDeleteConv(c.id)
                }}
              >
                ×
              </button>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          Hybrid RAG · Vector + Graph · LLM thinking
        </div>
      </aside>

      {/* Main */}
      <main className="main">
        <header className="topbar">
          <div className="topbar-left">
            <div className="chat-title">{active?.title ?? 'Chat'}</div>
          </div>
          <div className="topbar-right">
            <select
              className="select"
              value={lawId}
              onChange={(e) => setLawId(e.target.value)}
              title="Lọc theo luật"
            >
              <option value="">Tất cả luật</option>
              {laws.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.label}
                </option>
              ))}
            </select>

            <div className="control-group" title="Chế độ suy luận của LLM">
              <span className="control-label">Thinking</span>
              {(['auto', 'on', 'off'] as ThinkingMode[]).map((m) => (
                <button
                  key={m}
                  className={`control-btn ${thinking === m ? 'active' : ''}`}
                  onClick={() => setThinking(m)}
                >
                  {m}
                </button>
              ))}
            </div>

            <div className="control-group" title="Hiển thị Vector/Graph context">
              <span className="control-label">Context</span>
              <button
                className={`control-btn ${showContext ? 'active' : ''}`}
                onClick={() => setShowContext((v) => !v)}
              >
                {showContext ? 'on' : 'off'}
              </button>
            </div>
          </div>
        </header>

        <div className="chat" ref={chatRef}>
          <div className="chat-inner">
            {isEmpty ? (
              <div className="empty-state">
                <h2>Hỏi gì về luật Viễn thông, CNTT, An ninh mạng?</h2>
                <p>
                  Pipeline kết hợp Vector RAG (Qdrant) + Graph RAG (Neo4j) +
                  LLM. Câu suy luận có thể bật <code>thinking</code> để mô
                  hình lập luận sâu hơn.
                </p>
                <div className="suggestion-grid">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      className="suggestion"
                      onClick={() => send(s)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m, i) => <MessageView key={i} m={m} />)
            )}
          </div>
        </div>

        <div className="composer-wrap">
          <div className="composer">
            <textarea
              ref={textareaRef}
              placeholder="Nhập câu hỏi pháp lý… (Enter để gửi, Shift+Enter để xuống dòng)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKey}
              rows={1}
            />
            <button
              className="send-btn"
              onClick={() => send()}
              disabled={!input.trim() || sending}
              title="Gửi"
            >
              ↑
            </button>
          </div>
          <div className="composer-hint">
            {lawId
              ? `Đang lọc theo: ${laws.find((l) => l.id === lawId)?.label ?? lawId}`
              : 'Tất cả luật'}
            {' · '}thinking={thinking}
            {' · '}context={showContext ? 'on' : 'off'}
          </div>
        </div>
      </main>
    </div>
  )
}

// ─── Subcomponents ──────────────────────────────────────────────
function MessageView({ m }: { m: Message }) {
  if (m.role === 'user') {
    return (
      <div className="msg user">
        <div className="msg-role">Bạn</div>
        <div className="msg-content">{m.text}</div>
      </div>
    )
  }
  if (m.role === 'error') {
    return (
      <div className="msg error">
        <div className="msg-role">Lỗi</div>
        <div className="msg-content">{m.text}</div>
      </div>
    )
  }

  // Assistant
  const refinedChanged =
    m.refined &&
    m.refined.refined &&
    m.refined.refined.trim() !== m.refined.original.trim()

  const hasThinking = m.thinking && m.thinking.length > 0
  const showThinkingLive = m.streaming && hasThinking && !m.answer

  return (
    <div className="msg assistant">
      <div className="msg-role">
        Trợ lý
        {m.intent && <span className="badge">{m.intent}</span>}
        {m.refined && (
          <span className={`badge ${m.thinking_used ? '' : 'muted'}`}>
            {m.thinking_used ? 'thinking' : 'no-thinking'}
          </span>
        )}
      </div>

      {refinedChanged && (
        <div className="msg-meta">↻ refined: {m.refined!.refined}</div>
      )}
      {m.refined?.objective && (
        <div className="msg-meta">🎯 mục tiêu: {m.refined.objective}</div>
      )}

      {hasThinking && (
        <details className="think" open={showThinkingLive}>
          <summary className="think-summary">
            <span className="think-icon">
              {m.streaming && !m.answer ? '✨' : '💭'}
            </span>
            <span className="think-label">
              {m.streaming && !m.answer ? 'Đang suy nghĩ…' : 'Suy nghĩ'}
            </span>
            <span className="think-len">
              {m.thinking.length.toLocaleString()} ký tự
            </span>
            <span className="chev">▸</span>
          </summary>
          <div className="think-body">{m.thinking}</div>
        </details>
      )}

      {m.streaming && !m.answer && !hasThinking ? (
        <div className="typing">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
        </div>
      ) : (
        <div className="msg-content">
          {m.answer}
          {m.streaming && m.answer && <span className="caret" />}
        </div>
      )}

      {m.context && (m.context.vector_context || m.context.graph_context) && (
        <details className="ctx">
          <summary className="ctx-summary">
            <span>Xem context retrieval</span>
            <span className="chev">▸</span>
          </summary>
          <div className="ctx-body">
            {m.context.vector_context && (
              <div className="ctx-section">
                <h4>VECTOR_CHUNKS</h4>
                <pre>{m.context.vector_context}</pre>
              </div>
            )}
            {m.context.graph_context && (
              <div className="ctx-section">
                <h4>GRAPH_CONTEXT</h4>
                <pre>{m.context.graph_context}</pre>
              </div>
            )}
            {m.context.graph_article_ids?.length ? (
              <div className="ctx-section">
                <h4>GRAPH_ARTICLE_IDS</h4>
                <pre>{m.context.graph_article_ids.join(', ')}</pre>
              </div>
            ) : null}
          </div>
        </details>
      )}
    </div>
  )
}
