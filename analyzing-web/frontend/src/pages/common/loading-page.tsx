type LoadingPageProps = {
  description: string
  label: string
  title: string
}

/** 通用全页加载状态，用于页面所需的基础上下文尚未就绪时。 */
export function LoadingPage({ description, label, title }: LoadingPageProps) {
  return (
    <SetupStateShell
      asideDescription="首次启动时，Web Host 会先读取本地配置，再决定是否需要进入连接配置。"
      asideTitle="正在准备工作区"
      description={description}
      icon={<LoaderCircle className="size-5 animate-spin" />}
      label={label}
      status="正在检查本地 Host"
      title={title}
    />
  )
}
import { LoaderCircle } from "lucide-react"

import { SetupStateShell } from "@/pages/common/components/setup-state-shell"
