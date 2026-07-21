import type { InvocationStatus, RuntimeStatus } from "@/api/engine-monitor"
import { Badge } from "@/components/ui/badge"

type MonitorStatusBadgeProps = {
  status: InvocationStatus | RuntimeStatus
}

const labels: Record<InvocationStatus | RuntimeStatus, string> = {
  created: "已创建",
  error: "异常",
  failed: "失败",
  loaded: "已加载",
  ready: "就绪",
  registered: "已注册",
  running: "执行中",
  skipped: "已跳过",
  succeeded: "成功",
  timeout: "超时",
  unavailable: "不可用",
}

/** 统一调用与插件运行状态的展示语义。 */
export function MonitorStatusBadge({ status }: MonitorStatusBadgeProps) {
  const variant =
    status === "failed" || status === "error" || status === "timeout"
      ? "destructive"
      : status === "succeeded" || status === "ready"
        ? "default"
        : "secondary"

  return <Badge variant={variant}>{labels[status]}</Badge>
}
