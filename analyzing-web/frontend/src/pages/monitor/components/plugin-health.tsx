import type { PluginStatusRecord } from "@/api/engine-monitor"
import { Badge } from "@/components/ui/badge"
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

type PluginHealthProps = {
  items: PluginStatusRecord[]
  onSelect: (item: PluginStatusRecord) => void
}

function getInstallLabel(status: PluginStatusRecord["install_status"]) {
  const labels = {
    discovered: "已发现",
    failed: "安装失败",
    installed: "已安装",
    removed: "已移除",
  }

  return labels[status]
}

/** 插件状态保持为辅助区，异常和不可用插件优先显示。 */
export function PluginHealth({ items, onSelect }: PluginHealthProps) {
  const sortedItems = [...items].sort((left, right) => {
    const leftPriority =
      left.runtime_status === "error"
        ? 0
        : left.runtime_status === "unavailable"
          ? 1
          : 2
    const rightPriority =
      right.runtime_status === "error"
        ? 0
        : right.runtime_status === "unavailable"
          ? 1
          : 2
    return (
      leftPriority - rightPriority ||
      left.plugin_id.localeCompare(right.plugin_id)
    )
  })

  return (
    <section>
      <div className="flex justify-end">
        <span className="text-xs text-muted-foreground">
          {items.length} 个已发现插件
        </span>
      </div>
      <ScrollArea className="mt-3 h-[min(58svh,42rem)] rounded-lg border border-border">
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-background/95 backdrop-blur">
            <TableRow>
              <TableHead>插件</TableHead>
              <TableHead>版本</TableHead>
              <TableHead>运行状态</TableHead>
              <TableHead>安装状态</TableHead>
              <TableHead>运行模式</TableHead>
              <TableHead>最近更新时间</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedItems.map((item) => (
              <TableRow
                className="cursor-pointer"
                key={`${item.plugin_id}-${item.version}`}
                onClick={() => onSelect(item)}
              >
                <TableCell>
                  <strong className="font-medium">{item.plugin_id}</strong>
                </TableCell>
                <TableCell className="font-mono text-xs text-muted-foreground">
                  {item.version ?? "--"}
                </TableCell>
                <TableCell>
                  <MonitorStatusBadge status={item.runtime_status} />
                </TableCell>
                <TableCell>
                  <Badge variant="outline">
                    {getInstallLabel(item.install_status)}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {item.detail.runtime_mode ?? "--"}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDateTime(item.updated_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </ScrollArea>
    </section>
  )
}
