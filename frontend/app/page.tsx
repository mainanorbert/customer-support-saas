import Image from "next/image"
import Link from "next/link"
import { SignInButton, SignedIn, SignedOut, UserButton } from "@clerk/nextjs"
import { ArrowRight, MessageSquare, Shield, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { cn } from "@/lib/utils"

/**
 * Renders a single marketing feature block with icon, title, and body copy.
 */
function feature_card({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof MessageSquare
  title: string
  description: string
}) {
  return (
    <div
      className={cn(
        "group relative rounded-2xl border border-border/80 bg-card/60 p-6 shadow-sm backdrop-blur-sm",
        "transition-colors hover:border-border hover:bg-card",
      )}
    >
      <div className="mb-4 inline-flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
        <Icon className="size-5" aria-hidden />
      </div>
      <h3 className="font-heading text-base font-semibold tracking-tight text-foreground">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
    </div>
  )
}

export default function Page() {
  return (
    <div className="relative flex min-h-svh flex-col overflow-hidden bg-background">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,oklch(0.25_0.06_264/0.12),transparent)] dark:bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,oklch(0.55_0.12_264/0.18),transparent)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-background"
        aria-hidden
      />

      <header className="relative z-10 border-b border-border/60 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex min-w-0 items-center gap-3 transition-opacity hover:opacity-90">
            <Image
              src="/cs-logo.png"
              alt="Customer support"
              width={200}
              height={52}
              className="h-9 w-auto max-w-[min(200px,42vw)] object-contain object-left sm:h-10"
              priority
            />
            <span className="hidden font-heading text-sm font-semibold tracking-tight text-foreground sm:inline">
              Support
            </span>
          </Link>
          <nav className="flex shrink-0 items-center gap-1 sm:gap-2">
            <ThemeToggle />
            <SignedOut>
              <SignInButton mode="modal">
                <Button size="sm" variant="outline">
                  Sign in
                </Button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <Button size="sm" className="hidden sm:inline-flex" asChild>
                <Link href="/chat">Chat</Link>
              </Button>
              <UserButton
                afterSignOutUrl="/"
                appearance={{
                  elements: { userButtonAvatarBox: "size-9 ring-2 ring-border/80" },
                }}
              />
            </SignedIn>
          </nav>
        </div>
      </header>

      <main className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-14 sm:px-6 sm:py-20 lg:px-8 lg:py-24">
        <div className="mx-auto max-w-3xl text-center">
          <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur-sm">
            <Sparkles className="size-3.5 text-primary" aria-hidden />
            AI-powered customer support
          </p>
          <h1 className="font-heading text-balance text-4xl font-semibold tracking-tight text-foreground sm:text-5xl sm:leading-[1.1]">
            Resolve inquiries faster with context that knows your business
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
            Connect channels, upload knowledge, and let your assistant draft accurate replies—while
            every tenant stays isolated and on-brand.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4">
            <SignedOut>
              <SignInButton mode="modal">
                <Button size="lg" className="min-w-[200px] gap-2 px-8 shadow-md">
                  Get started
                  <ArrowRight className="size-4" aria-hidden />
                </Button>
              </SignInButton>
              <Button size="lg" variant="outline" className="min-w-[200px]" asChild>
                <Link href="#features">Learn more</Link>
              </Button>
            </SignedOut>
            <SignedIn>
              <Button size="lg" className="min-w-[220px] gap-2 px-8 shadow-md" asChild>
                <Link href="/chat">
                  Open support chat
                  <ArrowRight className="size-4" aria-hidden />
                </Link>
              </Button>
            </SignedIn>
          </div>
        </div>

        <section
          id="features"
          className="mx-auto mt-20 grid max-w-5xl gap-5 sm:mt-24 sm:grid-cols-2 lg:grid-cols-3 lg:gap-6"
          aria-labelledby="features-heading"
        >
          <h2 id="features-heading" className="sr-only">
            Product features
          </h2>
          {feature_card({
            icon: MessageSquare,
            title: "Omnichannel inbox",
            description:
              "Monitor email and messaging in one place so nothing slips through—and responses stay consistent.",
          })}
          {feature_card({
            icon: Sparkles,
            title: "Grounded answers",
            description:
              "Retrieve tenant-specific context to generate replies that reflect your policies and documentation.",
          })}
          {feature_card({
            icon: Shield,
            title: "Tenant isolation",
            description:
              "Each organization’s data and embeddings stay separate so customers only see what belongs to them.",
          })}
        </section>
      </main>

      <footer className="relative z-10 border-t border-border/60 bg-muted/30 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 text-center text-xs text-muted-foreground sm:flex-row sm:text-left sm:px-6 lg:px-8">
          <p>© {new Date().getFullYear()} Customer support platform</p>
          <p className="font-mono">
            Theme: header toggle or{" "}
            <kbd className="rounded border border-border bg-background px-1.5 py-0.5">d</kbd>
          </p>
        </div>
      </footer>
    </div>
  )
}
