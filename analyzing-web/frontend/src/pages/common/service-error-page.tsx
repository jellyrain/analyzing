import { CircleAlert } from "lucide-react"

import { Button } from "@/components/ui/button"
import { SetupStateShell } from "@/pages/common/components/setup-state-shell"

type ServiceErrorPageProps = {
  description: string
  label: string
  onRetry?: () => void
  title: string
}

/** 通用服务不可用页面，调用方可以按需提供重试操作。 */
export function ServiceErrorPage({
  description,
  label,
  onRetry,
  title,
}: ServiceErrorPageProps) {
  return (
    <SetupStateShell
      action={onRetry ? <Button onClick={onRetry}>重新尝试</Button> : undefined}
      asideDescription="请确认 Analyzing Web Host 已启动，并且当前浏览器连接到了正确的本地服务地址。"
      asideTitle="暂时无法继续"
      description={description}
      icon={<CircleAlert className="size-5" />}
      label={label}
      status="Host 服务不可用"
      statusTone="error"
      title={title}
    />
  )
}
