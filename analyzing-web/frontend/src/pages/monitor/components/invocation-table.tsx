import type { PluginInvocationRecord } from "@/api/engine-monitor"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { MonitorStatusBadge } from "@/pages/monitor/components/monitor-status-badge"
import { formatDateTime } from "@/lib/format"

type InvocationTableProps = {
  items: PluginInvocationRecord[]
  onSelect: (item: PluginInvocationRecord) => void
}

function formatLatency(value: number | null) {
  return value === null ? "--" : `${value} ms`
}

/** 插件调用流，列表单位是单次插件调用而不是前端猜测的规则执行。 */
export function InvocationTable({ items, onSelect }: InvocationTableProps) {
  if (items.length === 0) {
    return <div className="grid min-h-72 place-items-center text-sm text-muted-foreground">尚无插件调用记录</div>
  }

  return (
    <ScrollArea className="h-[min(50svh,38rem)] rounded-lg border border-border">
      <Table>
        <TableHeader className="sticky top-0 z-10 bg-background/95 backdrop-blur">
          <TableRow>
            <TableHead>状态</TableHead>
            <TableHead>插件 / 操作</TableHead>
            <TableHead>执行 ID</TableHead>
            <TableHead>模式</TableHead>
            <TableHead>耗时</TableHead>
            <TableHead>开始时间</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow
              className="cursor-pointer"
              key={item.invocation_id}
              onClick={() => onSelect(item)}
            >
              <TableCell><MonitorStatusBadge status={item.status} /></TableCell>
              <TableCell>
                <div className="grid gap-0.5">
                  <strong className="font-medium">{item.plugin_id}</strong>
                  <span className="text-xs text-muted-foreground">{item.detail.operation ?? "plugin.invoke"}</span>
                </div>
              </TableCell>
              <TableCell className="font-mono text-xs text-muted-foreground">{item.execution_id.slice(0, 12)}</TableCell>
              <TableCell className="text-muted-foreground">{item.runtime_mode}</TableCell>
              <TableCell>{formatLatency(item.latency_ms)}</TableCell>
              <TableCell className="text-muted-foreground">{formatDateTime(item.started_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </ScrollArea>
  )
}
