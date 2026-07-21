import { RefreshCw } from "lucide-react"

import type {
  AccessLogRecord,
  InvocationStatus,
  PluginInvocationRecord,
  RuntimeMode,
} from "@/api/engine-monitor"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AccessTable } from "@/pages/monitor/components/access-table"
import { InvocationTable } from "@/pages/monitor/components/invocation-table"
import { MonitorDetailSheet } from "@/pages/monitor/components/monitor-detail-sheet"
import type { MonitorTab } from "@/pages/monitor/types"

type InvocationWorkspaceProps = {
  accessError: string | null
  accessItems: AccessLogRecord[]
  activeTab: MonitorTab
  invocationItems: PluginInvocationRecord[]
  selectedAccess: AccessLogRecord | null
  selectedInvocation: PluginInvocationRecord | null
  onAccessPathChange: (path: string) => void
  onCloseDetail: () => void
  onInvocationExecutionChange: (executionId: string) => void
  onInvocationModeChange: (runtimeMode: RuntimeMode | undefined) => void
  onInvocationPluginChange: (pluginId: string) => void
  onInvocationStatusChange: (status: InvocationStatus | undefined) => void
  onRefresh: () => void
  onSelectAccess: (item: AccessLogRecord) => void
  onSelectInvocation: (item: PluginInvocationRecord) => void
  onTabChange: (tab: MonitorTab) => void
}

const invocationStatuses: InvocationStatus[] = [
  "created",
  "running",
  "succeeded",
  "failed",
  "timeout",
  "skipped",
]
const runtimeModes: RuntimeMode[] = ["inproc", "subprocess", "remote"]

/** 插件调用与 API 访问记录共用一个子页面，详情按需使用 Sheet 打开。 */
export function InvocationWorkspace({
  accessError,
  accessItems,
  activeTab,
  invocationItems,
  selectedAccess,
  selectedInvocation,
  onAccessPathChange,
  onCloseDetail,
  onInvocationExecutionChange,
  onInvocationModeChange,
  onInvocationPluginChange,
  onInvocationStatusChange,
  onRefresh,
  onSelectAccess,
  onSelectInvocation,
  onTabChange,
}: InvocationWorkspaceProps) {
  return (
    <section className="pt-7">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.14em] text-primary">
            REQUEST STREAM
          </p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.02em]">
            调用记录
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            插件调用和 Engine API 访问日志均支持服务端筛选。
          </p>
        </div>
        <Button onClick={onRefresh} variant="outline">
          <RefreshCw />
          刷新数据
        </Button>
      </header>

      <Tabs
        className="mt-6"
        onValueChange={(value) => onTabChange(value as MonitorTab)}
        value={activeTab}
      >
        <TabsList>
          <TabsTrigger value="invocations">插件调用</TabsTrigger>
          <TabsTrigger value="access">API 访问</TabsTrigger>
        </TabsList>
        <TabsContent className="mt-5" value="invocations">
          <div className="flex flex-wrap gap-2 rounded-lg border border-border bg-muted/25 p-3">
            <Input
              className="min-w-64 flex-1"
              onChange={(event) =>
                onInvocationExecutionChange(event.target.value)
              }
              placeholder="筛选执行 ID"
            />
            <Input
              className="min-w-64 flex-1"
              onChange={(event) => onInvocationPluginChange(event.target.value)}
              placeholder="筛选插件 ID"
            />
            <Select
              defaultValue="all"
              onValueChange={(value) =>
                onInvocationStatusChange(
                  value === "all" ? undefined : (value as InvocationStatus)
                )
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {invocationStatuses.map((status) => (
                  <SelectItem key={status} value={status}>
                    {status}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              defaultValue="all"
              onValueChange={(value) =>
                onInvocationModeChange(
                  value === "all" ? undefined : (value as RuntimeMode)
                )
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部模式</SelectItem>
                {runtimeModes.map((mode) => (
                  <SelectItem key={mode} value={mode}>
                    {mode}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="mt-4">
            <InvocationTable
              items={invocationItems}
              onSelect={onSelectInvocation}
            />
          </div>
        </TabsContent>
        <TabsContent className="mt-5" value="access">
          <div className="flex flex-wrap gap-2 rounded-lg border border-border bg-muted/25 p-3">
            <Input
              className="min-w-80 flex-1"
              onChange={(event) => onAccessPathChange(event.target.value)}
              placeholder="筛选请求路径"
            />
          </div>
          {accessError ? (
            <p className="mt-4 text-sm text-destructive">{accessError}</p>
          ) : (
            <div className="mt-4">
              <AccessTable items={accessItems} onSelect={onSelectAccess} />
            </div>
          )}
        </TabsContent>
      </Tabs>

      <MonitorDetailSheet
        access={selectedAccess}
        invocation={selectedInvocation}
        onOpenChange={(open) => {
          if (!open) onCloseDetail()
        }}
      />
    </section>
  )
}
