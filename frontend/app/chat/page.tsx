"use client"

import { UserButton } from "@clerk/nextjs"
import Link from "next/link"
import { useCallback, useEffect, useRef, useState } from "react"
import { ArrowLeft, Loader2, SendHorizontal } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { cn } from "@/lib/utils"

type ChatRole = "user" | "assistant"

type ChatMessage = {
  id: string
  role: ChatRole
  content: string
}

type AgentChatResponse = {
  reply: string
}

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
  const [messages, set_messages] = useState<ChatMessage[]>([])
  const [draft, set_draft] = useState("")
  const [pending, set_pending] = useState(false)
  const [error, set_error] = useState<string | null>(null)
  const list_end_ref = useRef<HTMLDivElement | null>(null)

  const scroll_to_bottom = useCallback(() => {
    list_end_ref.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  useEffect(() => {
    scroll_to_bottom()
  }, [messages, scroll_to_bottom])

  const send_message = useCallback(async () => {
    const text = draft.trim()
    if (!text || pending) return

    set_error(null)
    set_pending(true)
    set_draft("")

    const user_message: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    }
    set_messages((prev) => [...prev, user_message])

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
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

      set_messages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: reply_text,
        },
      ])
    } catch {
      set_error("Network error while sending your message.")
    } finally {
      set_pending(false)
    }
  }, [draft, pending])

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
              Signed-in users only; requests include a Clerk session token.
            </p>
          </div>
          <ThemeToggle />
          <UserButton afterSignOutUrl="/" />
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-3 px-4 py-4">
        <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border bg-card">
          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground">
                Ask a question to get a reply from the support agent.
              </p>
            ) : (
              messages.map((m) => (
                <div
                  key={m.id}
                  className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}
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
                </div>
              ))
            )}
            <div ref={list_end_ref} />
          </div>

          {error ? (
            <div className="border-t border-border px-4 py-2 text-xs text-destructive">
              {error}
            </div>
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
              disabled={pending}
              onChange={(e) => set_draft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  void send_message()
                }
              }}
              placeholder="Type your message… (Enter to send, Shift+Enter for newline)"
              className="field-sizing-content min-h-[4.5rem] resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none ring-ring/50 focus-visible:border-ring focus-visible:ring-3 disabled:opacity-50"
            />
            <div className="flex justify-end">
              <Button type="submit" disabled={pending || !draft.trim()}>
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