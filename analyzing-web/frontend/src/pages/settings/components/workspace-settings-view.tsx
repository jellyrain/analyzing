import { LoaderCircle, Plug, RefreshCw, Save, Server } from "lucide-react"

import type { HostConfig } from "@/api/host"
import { Button } from "@/components/ui/button"
import { AppShell } from "@/layout/app-shell"
import { FeedbackLine } from "@/pages/settings/components/feedback-line"
import {
  EngineOriginField,
  MonitorRefreshField,
} from "@/pages/settings/components/host-config-fields"
import type { Feedback, HostConfigActions } from "@/pages/settings/types"

type WorkspaceSettingsViewProps = HostConfigActions & {
  feedback: Feedback | null
  form: HostConfig
  isBusy: boolean
  isDirty: boolean
  isSaving: boolean
  isTesting: boolean
}

/** 配置完成后的设置工作区，后续与规则、监控共用 AppShell。 */
export function WorkspaceSettingsView({
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
}: WorkspaceSettingsViewProps) {
  return (
    <AppShell activePage="settings">
      <div className="mx-auto flex min-h-full w-full max-w-6xl flex-col px-5 py-7 sm:px-8 sm:py-10 lg:px-12">
        <header className="flex flex-wrap items-start justify-between gap-5 border-b border-border pb-6">
          <div>
            <p className="text-xs font-semibold tracking-[0.14em] text-primary">SYSTEM CONFIG</p>
            <h1 className="mt-3 text-balance text-2xl font-semibold tracking-[-0.03em] sm:text-3xl">系统配置</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">管理当前 Web Host 的连接地址与监控偏好。Engine 自身运行配置在这里仅作为后续只读信息展示。</p>
          </div>
          <span className="rounded-full bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary">{isDirty ? "存在未保存修改" : "配置已保存"}</span>
        </header>

        <form className="flex flex-1 flex-col" onSubmit={(event) => { event.preventDefault(); onSave() }}>
          <div className="max-w-4xl space-y-8 py-8">
            <section className="grid gap-5 border-b border-border pb-8 md:grid-cols-[11rem_minmax(0,1fr)]">
              <div>
                <div className="flex items-center gap-2 text-primary"><Server className="size-4" /><h2 className="text-sm font-semibold text-foreground">Engine 连接</h2></div>
                <p className="mt-2 text-xs leading-5 text-muted-foreground">Host 保存根地址，并统一转发所有页面请求。</p>
              </div>
              <div>
                <EngineOriginField form={form} idPrefix="workspace" onUpdate={onUpdate} />
                <p className="mt-2 text-xs leading-5 text-muted-foreground">不要包含 /api。测试连接会请求 Engine 的 /api/system/info。</p>
              </div>
            </section>
            <section className="grid gap-5 border-b border-border pb-8 md:grid-cols-[11rem_minmax(0,1fr)]">
              <div>
                <div className="flex items-center gap-2 text-primary"><RefreshCw className="size-4" /><h2 className="text-sm font-semibold text-foreground">运行监控</h2></div>
                <p className="mt-2 text-xs leading-5 text-muted-foreground">此值只影响 Web 页面自动刷新，不会修改 Engine。</p>
              </div>
              <div>
                <MonitorRefreshField form={form} idPrefix="workspace" onUpdate={onUpdate} />
                <p className="mt-2 text-xs leading-5 text-muted-foreground">当前将每 {form.monitor_refresh_seconds || "-"} 秒刷新一次调用与插件状态。</p>
              </div>
            </section>
            <FeedbackLine feedback={feedback} />
          </div>
          <footer className="sticky bottom-0 mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-border bg-background/88 py-5 backdrop-blur-xl">
            <Button disabled={isBusy} onClick={onRestore} type="button" variant="ghost">恢复已保存配置</Button>
            <div className="flex flex-wrap gap-2">
              <Button disabled={isBusy} onClick={onTest} type="button" variant="outline">{isTesting ? <LoaderCircle className="animate-spin" /> : <Plug />}测试连接</Button>
              <Button disabled={isBusy} type="submit">{isSaving ? <LoaderCircle className="animate-spin" /> : <Save />}保存配置</Button>
            </div>
          </footer>
        </form>
      </div>
    </AppShell>
  )
}
