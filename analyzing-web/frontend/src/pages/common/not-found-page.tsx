import { Link } from "react-router"

import { SetupStateShell } from "@/pages/common/components/setup-state-shell"

/** 通用不存在页面，后续增加业务路由时不需要在各页面重复处理。 */
export function NotFoundPage() {
  return (
    <SetupStateShell
      action={<Link className="text-sm font-medium text-primary underline-offset-4 hover:underline" to="/settings">返回系统配置</Link>}
      asideDescription="当前地址没有对应页面。完成首次连接后，规则与监控等工作区会在这里扩展。"
      asideTitle="当前页面不存在"
      description="请从系统配置重新进入工作区，或检查访问地址是否正确。"
      icon={<span className="text-sm font-semibold">404</span>}
      label="ROUTE NOT FOUND"
      status="等待有效路由"
      title="页面不存在"
    />
  )
}
