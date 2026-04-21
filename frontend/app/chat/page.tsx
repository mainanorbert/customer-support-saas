"use client"

import { UserButton } from "@clerk/nextjs"
import Link from "next/link"
import { useCallback, useEffect, useRef, useState } from "react"
import { ArrowLeft, Building2, Loader2, SendHorizontal } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { cn } from "@/lib/utils"

type ChatRole = "user" | "assistant"

type ChatMessage = {
  id: string
  role: ChatRole
  content: string
  grounded: boolean | null
}

type CompanyResponse = {
  id: string
  name: string
  email: string
  owner_id: string
  created_at: string
}

type AgentChatResponse = {
  reply: string
  grounded?: boolean
}

/**
 * Builds a human-readable error string from common API JSON shapes.
 */
function format_error_payload(data: unknown): string {
  if (typeof data !== "object" || data === null) return "Request failed"
  const err = (data as { error?: unknown }).error
  if (typeof err === "string") return err
  const detail = (data as { detail?: unknown }).detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String((item as { msg: unknown }).msg)
        }
        return JSON.stringify(item)
      })
      .join("; ")
  }
  return "Request failed"
}

export default function ChatPage() {
  const [companies, set_companies] = useState<CompanyResponse[]>([])
  const [selected_company_id, set_selected_company_id] = useState<string | null>(null)
  const [messages, set_messages] = useState<ChatMessage[]>([])
  const [draft, set_draft] = useState("")
  const [pending, set_pending] = useState(false)
  const [page_loading, set_page_loading] = useState(true)
  const [error, set_error] = useState<string | null>(null)
  const list_end_ref = useRef<HTMLDivElement | null>(null)

  const scroll_to_bottom = useCallback(() => {
    list_end_ref.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  useEffect(() => {
    scroll_to_bottom()
  }, [messages, scroll_to_bottom])

  const load_companies = useCallback(async () => {
    const res = await fetch("/api/ingestion/companies")
    const data: unknown = await res.json().catch(() => ({}))
    if (!res.ok) {
      set_error(format_error_payload(data))
      return
    }
    if (!Array.isArray(data)) {
      set_error("Unexpected companies response")
      return
    }
    const list = data as CompanyResponse[]
    set_companies(list)
    set_selected_company_id((prev) => {
      if (list.length === 0) return null
      if (prev && list.some((c) => c.id === prev)) return prev
      return list[0].id
    })
  }, [])

  const bootstrap = useCallback(async () => {
    set_page_loading(true)
    set_error(null)
    try {
      const reg = await fetch("/api/ingestion/register", { method: "POST" })
      const reg_data: unknown = await reg.json().catch(() => ({}))
      if (!reg.ok) {
        set_error(format_error_payload(reg_data))
        return
      }
      await load_companies()
    } finally {
      set_page_loading(false)
    }
  }, [load_companies])

  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  useEffect(() => {
    set_messages([])
    set_error(null)
  }, [selected_company_id])

  const selected_company = companies.find((c) => c.id === selected_company_id)

  const send_message = useCallback(async () => {
    const text = draft.trim()
    if (!text || pending || !selected_company_id) return

    set_error(null)
    set_pending(true)
    set_draft("")

    const user_message: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      grounded: null,
    }
    set_messages((prev) => [...prev, user_message])

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_id: selected_company_id, message: text }),
      })

      const data: unknown = await res.json().catch(() => ({}))

      if (!res.ok) {
        set_error(format_error_payload(data))
        return
      }

      const parsed = data as Partial<AgentChatResponse>
      const reply_text = parsed.reply
      if (typeof reply_text !== "string") {
        set_error("Unexpected response from server")
        return
      }

      const grounded = typeof parsed.grounded === "boolean" ? parsed.grounded : null

      set_messages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: reply_text,
          grounded,
        },
      ])
    } catch {
      set_error("Network error while sending your message.")
    } finally {
      set_pending(false)
    }
  }, [draft, pending, selected_company_id])

  return (
    <div className="flex min-h-svh flex-col bg-background">
      <header className="border-b border-border px-4 py-3">
        <div className="mx-auto flex max-w-2xl items-center gap-3">
          <Button variant="ghost" size="icon-sm" asChild>
            <Link href="/" aria-label="Back to home">
              <ArrowLeft />
            </Link>
          </Button>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-sm font-medium">Support chat</h1>
            <p className="truncate text-xs text-muted-foreground">
              Answers use your uploaded PDFs (RAG) for the company you select below.
            </p>
          </div>
          <Button variant="outline" size="sm" className="hidden shrink-0 sm:inline-flex" asChild>
            <Link href="/documents">Documents</Link>
          </Button>
          <ThemeToggle />
          <UserButton afterSignOutUrl="/" />
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-3 px-4 py-4">
        {/* Company selector */}
        <section className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
            <Building2 className="size-4 text-primary" aria-hidden />
            Knowledge base company
          </div>
          {page_loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" aria-hidden />
              Loading companies…
            </div>
          ) : companies.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No companies yet.{" "}
              <Link href="/documents" className="font-medium text-primary underline-offset-4 hover:underline">
                Create a company and upload PDFs
              </Link>{" "}
              before chatting.
            </p>
          ) : (
            <div className="flex flex-col gap-1.5">
              <label htmlFor="chat-company" className="sr-only">
                Select company for RAG
              </label>
              <select
                id="chat-company"
                value={selected_company_id ?? ""}
                onChange={(e) => set_selected_company_id(e.target.value || null)}
                className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none ring-ring/50 focus-visible:border-ring focus-visible:ring-3"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.email})
                  </option>
                ))}
              </select>
              {selected_company && (
                <p className="text-xs text-muted-foreground">
                  The assistant retrieves context only from{" "}
                  <span className="font-medium text-foreground">{selected_company.name}</span>
                  &apos;s embedded documents.
                </p>
              )}
            </div>
          )}
        </section>

        <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border bg-card">
          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground">
                {selected_company_id
                  ? "Ask a question about this company’s knowledge base."
                  : "Select a company above to start."}
              </p>
            ) : (
              messages.map((m) => (
                <div
                  key={m.id}
                  className={cn("flex flex-col gap-1", m.role === "user" ? "items-end" : "items-start")}
                >
                  <div
                    className={cn(
                      "max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap",
                      m.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-foreground",
                    )}
                  >
                    {m.content}
                  </div>
                  {m.role === "assistant" && m.grounded !== null && (
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[10px] font-medium",
                        m.grounded
                          ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400"
                          : "bg-amber-500/15 text-amber-800 dark:text-amber-300",
                      )}
                    >
                      {m.grounded ? "From knowledge base" : "No close match in knowledge base"}
                    </span>
                  )}
                </div>
              ))
            )}
            <div ref={list_end_ref} />
          </div>

          {error ? (
            <div className="border-t border-border px-4 py-2 text-xs text-destructive">{error}</div>
          ) : null}

          <form
            className="flex flex-col gap-2 border-t border-border p-3"
            onSubmit={(e) => {
              e.preventDefault()
              void send_message()
            }}
          >
            <label htmlFor="chat-input" className="sr-only">
              Message
            </label>
            <textarea
              id="chat-input"
              rows={3}
              value={draft}
              disabled={pending || !selected_company_id}
              onChange={(e) => set_draft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  void send_message()
                }
              }}
              placeholder={
                selected_company_id
                  ? "Type your message… (Enter to send, Shift+Enter for newline)"
                  : "Select a company above first…"
              }
              className="field-sizing-content min-h-[4.5rem] resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none ring-ring/50 focus-visible:border-ring focus-visible:ring-3 disabled:opacity-50"
            />
            <div className="flex justify-end">
              <Button type="submit" disabled={pending || !draft.trim() || !selected_company_id}>
                {pending ? (
                  <>
                    <Loader2 className="animate-spin" data-icon="inline-start" />
                    Sending
                  </>
                ) : (
                  <>
                    <SendHorizontal data-icon="inline-start" />
                    Send
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}
