import type { AccessLogRecord, PluginInvocationRecord } from "@/api/engine-monitor"
import { Badge } from "@/components/ui/badge"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { MonitorStatusBadge } from "@/pages/monitor/components/monitor-status-badge"
import { formatDateTime } from "@/lib/format"

type MonitorDetailSheetProps = {
  access: AccessLogRecord | null
  invocation: PluginInvocationRecord | null
  onOpenChange: (open: boolean) => void
}

function DetailRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="grid grid-cols-[7rem_minmax(0,1fr)] gap-3 border-b border-border py-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="min-w-0 break-all">{value ?? "--"}</span>
    </div>
  )
}

/** 仅在选中一条记录时打开，避免常驻详情栏压缩主表格。 */
export function MonitorDetailSheet({ access, invocation, onOpenChange }: MonitorDetailSheetProps) {
  const open = invocation !== null || access !== null

  return (
    <Sheet onOpenChange={onOpenChange} open={open}>
      <SheetContent className="w-full gap-0 p-0 sm:max-w-xl">
        {invocation ? (
          <>
            <SheetHeader className="border-b border-border">
              <div className="flex items-center justify-between gap-4"><SheetTitle>插件调用详情</SheetTitle><MonitorStatusBadge status={invocation.status} /></div>
              <SheetDescription>{invocation.plugin_id} / {invocation.detail.operation ?? "plugin.invoke"}</SheetDescription>
            </SheetHeader>
            <div className="overflow-auto p-4">
              <DetailRow label="调用 ID" value={invocation.invocation_id} />
              <DetailRow label="执行 ID" value={invocation.execution_id} />
              <DetailRow label="Trace ID" value={invocation.detail.trace_id} />
              <DetailRow label="运行模式" value={invocation.runtime_mode} />
              <DetailRow label="插件版本" value={invocation.version} />
              <DetailRow label="开始时间" value={formatDateTime(invocation.started_at)} />
              <DetailRow label="结束时间" value={formatDateTime(invocation.finished_at)} />
              <DetailRow label="耗时" value={invocation.latency_ms === null ? null : `${invocation.latency_ms} ms`} />
              <DetailRow label="输入大小" value={invocation.input_size} />
              <DetailRow label="输出数量" value={invocation.output_count} />
              <DetailRow label="错误信息" value={invocation.error_message} />
              <pre className="mt-5 overflow-auto rounded-lg bg-muted p-3 text-xs leading-5 text-muted-foreground">{JSON.stringify(invocation.detail, null, 2)}</pre>
            </div>
          </>
        ) : access ? (
          <>
            <SheetHeader className="border-b border-border">
              <div className="flex items-center justify-between gap-4"><SheetTitle>API 访问详情</SheetTitle><Badge>{access.status_code}</Badge></div>
              <SheetDescription>{access.method} {access.path}</SheetDescription>
            </SheetHeader>
            <div className="overflow-auto p-4">
              <DetailRow label="访问 ID" value={access.access_id} />
              <DetailRow label="Trace ID" value={access.trace_id} />
              <DetailRow label="客户端" value={access.client_ip} />
              <DetailRow label="创建时间" value={formatDateTime(access.created_at)} />
              <DetailRow label="请求大小" value={access.request_size} />
              <DetailRow label="响应大小" value={access.response_size} />
              <DetailRow label="耗时" value={access.latency_ms === null ? null : `${access.latency_ms} ms`} />
              <pre className="mt-5 overflow-auto rounded-lg bg-muted p-3 text-xs leading-5 text-muted-foreground">{JSON.stringify(access.detail, null, 2)}</pre>
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  )
}
