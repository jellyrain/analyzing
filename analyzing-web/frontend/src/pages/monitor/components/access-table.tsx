import type { AccessLogRecord } from "@/api/engine-monitor"
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
import { formatDateTime } from "@/lib/format"

type AccessTableProps = {
  items: AccessLogRecord[]
  onSelect: (item: AccessLogRecord) => void
}

function getStatusVariant(statusCode: number) {
  if (statusCode >= 500) return "destructive"
  if (statusCode >= 400) return "secondary"
  return "default"
}

/** Engine API 访问日志列表。 */
export function AccessTable({ items, onSelect }: AccessTableProps) {
  if (items.length === 0) {
    return <div className="grid min-h-72 place-items-center text-sm text-muted-foreground">尚无 API 访问日志</div>
  }

  return (
    <ScrollArea className="h-[min(50svh,38rem)] rounded-lg border border-border">
      <Table>
        <TableHeader className="sticky top-0 z-10 bg-background/95 backdrop-blur">
          <TableRow>
            <TableHead>方法</TableHead>
            <TableHead>路径</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>耗时</TableHead>
            <TableHead>客户端</TableHead>
            <TableHead>时间</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow className="cursor-pointer" key={item.access_id} onClick={() => onSelect(item)}>
              <TableCell className="font-mono text-xs">{item.method}</TableCell>
              <TableCell className="max-w-96 truncate font-mono text-xs">{item.path}</TableCell>
              <TableCell><Badge variant={getStatusVariant(item.status_code)}>{item.status_code}</Badge></TableCell>
              <TableCell>{item.latency_ms === null ? "--" : `${item.latency_ms} ms`}</TableCell>
              <TableCell className="text-muted-foreground">{item.client_ip ?? "--"}</TableCell>
              <TableCell className="text-muted-foreground">{formatDateTime(item.created_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </ScrollArea>
  )
}
