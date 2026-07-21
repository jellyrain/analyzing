import type { ReactNode } from "react"

import { ThemeToggle } from "@/components/theme-toggle"

type SetupStateShellProps = {
  action?: ReactNode
  asideDescription: string
  asideTitle: string
  description: string
  icon: ReactNode
  label: string
  status: string
  statusTone?: "default" | "error"
  title: string
}

/** 连接前的通用状态壳，与首次系统配置页保持同一视觉语言。 */
export function SetupStateShell({
  action,
  asideDescription,
  asideTitle,
  description,
  icon,
  label,
  status,
  statusTone = "default",
  title,
}: SetupStateShellProps) {
  const statusClassName =
    statusTone === "error" ? "bg-destructive" : "bg-primary"

  return (
    <main className="relative h-full overflow-auto bg-[radial-gradient(circle_at_12%_12%,oklch(0.94_0.04_246)_0,transparent_31%),radial-gradient(circle_at_87%_88%,oklch(0.95_0.025_220)_0,transparent_28%)] px-4 py-5 text-foreground sm:px-8 sm:py-8">
      <div className="absolute top-6 right-6 sm:top-9 sm:right-9">
        <ThemeToggle />
      </div>
      <section className="mx-auto grid min-h-[calc(100svh-2.5rem)] max-w-6xl overflow-hidden rounded-2xl border border-primary/15 bg-background/68 backdrop-blur-xl lg:grid-cols-[minmax(18rem,0.78fr)_minmax(31rem,1.22fr)]">
        <aside className="flex flex-col justify-between border-b border-primary/12 bg-primary/[0.045] px-6 py-7 lg:border-r lg:border-b-0 lg:px-9 lg:py-10">
          <div className="space-y-10">
            <div className="flex items-center gap-3">
              <div className="grid size-9 place-items-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
                A
              </div>
              <div className="leading-tight">
                <p className="text-sm font-semibold tracking-[0.08em]">
                  ANALYZING
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  文档解析工作台
                </p>
              </div>
            </div>
            <div className="space-y-4">
              <p className="text-xs font-semibold tracking-[0.16em] text-primary">
                WEB HOST / STATUS
              </p>
              <h1 className="max-w-sm text-3xl font-semibold tracking-[-0.035em] text-balance sm:text-4xl">
                {asideTitle}
              </h1>
              <p className="max-w-sm text-sm leading-7 text-muted-foreground">
                {asideDescription}
              </p>
            </div>
          </div>
          <div className="mt-10 space-y-3 border-t border-primary/12 pt-5 text-xs leading-5 text-muted-foreground">
            <p className="flex items-center gap-2 text-foreground">
              <span className={`size-2 rounded-full ${statusClassName}`} />
              {status}
            </p>
            <p>本地 Host 负责管理连接配置与页面请求。</p>
          </div>
        </aside>

        <section className="flex min-w-0 items-center px-6 py-7 sm:px-9 sm:py-10 lg:px-12">
          <div className="w-full max-w-xl">
            <div className="border-b border-border pb-6">
              <p className="text-xs font-semibold tracking-[0.14em] text-primary">
                {label}
              </p>
            </div>
            <div className="py-12 sm:py-16">
              <div className="mb-6 grid size-11 place-items-center rounded-lg bg-primary/10 text-primary">
                {icon}
              </div>
              <h2 className="text-2xl font-semibold tracking-[-0.03em] text-balance sm:text-3xl">
                {title}
              </h2>
              <p className="mt-3 max-w-lg text-sm leading-7 text-muted-foreground">
                {description}
              </p>
              {action ? <div className="mt-8">{action}</div> : null}
            </div>
          </div>
        </section>
      </section>
    </main>
  )
}
