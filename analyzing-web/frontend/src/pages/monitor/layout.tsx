import { Navigate, Outlet } from "react-router"

import { getApiErrorMessage } from "@/api/http"
import { useHostBootstrap } from "@/features/connection/use-host-bootstrap"
import { AppShell } from "@/layout/app-shell"
import { LoadingPage } from "@/pages/common/loading-page"
import { ServiceErrorPage } from "@/pages/common/service-error-page"

/** 监控模块父布局：负责 Host 守卫与三个子页面共享的应用壳。 */
export function MonitorLayout() {
  const bootstrapQuery = useHostBootstrap()

  if (bootstrapQuery.isPending) {
    return (
      <LoadingPage
        description="正在读取 Host 连接配置。"
        label="ANALYZING WEB"
        title="正在准备运行监控"
      />
    )
  }

  if (bootstrapQuery.isError) {
    return (
      <ServiceErrorPage
        description={getApiErrorMessage(
          bootstrapQuery.error,
          "请确认 Web Host 后端已经启动。"
        )}
        label="HOST UNAVAILABLE"
        onRetry={() => void bootstrapQuery.refetch()}
        title="无法打开运行监控"
      />
    )
  }

  if (!bootstrapQuery.data.configured) {
    return <Navigate replace to="/settings" />
  }

  return (
    <AppShell activePage="monitor">
      <div className="h-full overflow-auto">
        <div className="mx-auto w-full max-w-7xl px-5 py-7 sm:px-8 sm:py-10 lg:px-12">
          <Outlet />
        </div>
      </div>
    </AppShell>
  )
}
