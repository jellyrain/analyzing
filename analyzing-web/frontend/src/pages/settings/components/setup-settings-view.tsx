import {
  LoaderCircle,
  Plug,
  RefreshCw,
  Save,
  Server,
  SlidersHorizontal,
} from "lucide-react"

import type { HostConfig } from "@/api/host"
import { ThemeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import { FeedbackLine } from "@/pages/settings/components/feedback-line"
import {
  EngineOriginField,
  MonitorRefreshField,
} from "@/pages/settings/components/host-config-fields"
import type { Feedback, HostConfigActions } from "@/pages/settings/types"

type SetupSettingsViewProps = HostConfigActions & {
  feedback: Feedback | null
  form: HostConfig
  isBusy: boolean
  isDirty: boolean
  isSaving: boolean
  isTesting: boolean
}

/** 未配置时的首次连接引导页。 */
export function SetupSettingsView({
  feedback,
  form,
  isBusy,
  isDirty,
  isSaving,
  isTesting,
  onRestore,
  onSave,
  onTest,
  onUpdate,
}: SetupSettingsViewProps) {
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
                WEB HOST / CONNECTION
              </p>
              <h1 className="max-w-sm text-3xl font-semibold tracking-[-0.035em] text-balance sm:text-4xl">
                先连接你的 Engine
              </h1>
              <p className="max-w-sm text-sm leading-7 text-muted-foreground">
                Web 页面不会直接访问 Engine。保存地址后，本地 Host
                会统一处理规则、监控与插件请求。
              </p>
            </div>
          </div>
          <div className="mt-10 space-y-3 border-t border-primary/12 pt-5 text-xs leading-5 text-muted-foreground">
            <p className="flex items-center gap-2 text-foreground">
              <span className="size-2 rounded-full bg-muted-foreground/45" />
              等待首次配置
            </p>
            <p>配置保存于 %APPDATA%\\Analyzing Web\\web.toml</p>
          </div>
        </aside>

        <section className="flex min-w-0 flex-col px-6 py-7 sm:px-9 sm:py-10 lg:px-12">
          <header className="flex items-start justify-between gap-6 border-b border-border pb-6">
            <div>
              <div className="flex items-center gap-2 text-primary">
                <SlidersHorizontal className="size-4" />
                <span className="text-xs font-semibold tracking-[0.14em]">
                  SYSTEM CONFIG
                </span>
              </div>
              <h2 className="mt-3 text-xl font-semibold tracking-[-0.025em]">
                系统配置
              </h2>
              <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
                填写 Engine 根地址。不要包含{" "}
                <code className="rounded bg-muted px-1 py-0.5 text-xs">
                  /api
                </code>
                。
              </p>
            </div>
            <span className="shrink-0 rounded-full bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary">
              {isDirty ? "未保存" : "未配置"}
            </span>
          </header>

          <form
            className="flex flex-1 flex-col"
            onSubmit={(event) => {
              event.preventDefault()
              onSave()
            }}
          >
            <div className="space-y-7 py-8">
              <section className="space-y-4">
                <div className="flex items-center gap-2">
                  <Server className="size-4 text-primary" />
                  <h3 className="text-sm font-semibold">Engine 连接</h3>
                </div>
                <EngineOriginField
                  form={form}
                  idPrefix="setup"
                  onUpdate={onUpdate}
                />
                <p className="text-xs leading-5 text-muted-foreground">
                  例如 http://127.0.0.1:8000。Host 测试时会请求
                  /api/system/info。
                </p>
              </section>
              <section className="space-y-4 border-t border-border pt-7">
                <div className="flex items-center gap-2">
                  <RefreshCw className="size-4 text-primary" />
                  <h3 className="text-sm font-semibold">监控刷新</h3>
                </div>
                <MonitorRefreshField
                  form={form}
                  idPrefix="setup"
                  onUpdate={onUpdate}
                />
                <p className="text-xs leading-5 text-muted-foreground">
                  监控页面默认每 {form.monitor_refresh_seconds || "-"}{" "}
                  秒拉取一次数据，可在后续页面临时调整。
                </p>
              </section>
              <div className="border-t border-border pt-6">
                <FeedbackLine feedback={feedback} />
              </div>
            </div>
            <footer className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-border pt-6">
              <Button
                disabled={isBusy}
                onClick={onRestore}
                type="button"
                variant="ghost"
              >
                恢复已保存配置
              </Button>
              <div className="flex flex-wrap gap-2">
                <Button
                  disabled={isBusy}
                  onClick={onTest}
                  type="button"
                  variant="outline"
                >
                  {isTesting ? (
                    <LoaderCircle className="animate-spin" />
                  ) : (
                    <Plug />
                  )}
                  测试连接
                </Button>
                <Button disabled={isBusy} type="submit">
                  {isSaving ? (
                    <LoaderCircle className="animate-spin" />
                  ) : (
                    <Save />
                  )}
                  保存配置
                </Button>
              </div>
            </footer>
          </form>
        </section>
      </section>
    </main>
  )
}
