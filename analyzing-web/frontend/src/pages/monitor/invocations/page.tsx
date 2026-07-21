import { getApiErrorMessage } from "@/api/http"
import { InvocationWorkspace } from "@/pages/monitor/components/invocation-workspace"
import { useMonitorAccessLogs } from "@/pages/monitor/hooks/use-monitor-access-logs"
import { useMonitorInvocations } from "@/pages/monitor/hooks/use-monitor-invocations"
import { useMonitorRefreshInterval } from "@/pages/monitor/hooks/use-monitor-refresh-interval"
import { useMonitorView } from "@/pages/monitor/hooks/use-monitor-view"

/** 插件调用与 Engine API 访问日志子页面。 */
export function MonitorInvocationsPage() {
  const view = useMonitorView()
  const { refreshMilliseconds } = useMonitorRefreshInterval(true)
  const invocationsQuery = useMonitorInvocations(
    view.invocationFilters,
    true,
    refreshMilliseconds
  )
  const accessQuery = useMonitorAccessLogs(
    view.accessFilters,
    true,
    refreshMilliseconds
  )

  const refreshAll = () => {
    void Promise.all([invocationsQuery.refetch(), accessQuery.refetch()])
  }

  return (
    <InvocationWorkspace
      accessError={
        accessQuery.isError
          ? getApiErrorMessage(accessQuery.error, "无法读取 API 访问日志。")
          : null
      }
      accessItems={accessQuery.data?.items ?? []}
      activeTab={view.activeTab}
      invocationItems={invocationsQuery.data?.items ?? []}
      onAccessPathChange={(path) =>
        view.setAccessFilters((filters) => ({ ...filters, offset: 0, path }))
      }
      onCloseDetail={() => {
        view.setSelectedAccess(null)
        view.setSelectedInvocation(null)
      }}
      onInvocationExecutionChange={(execution_id) =>
        view.setInvocationFilters((filters) => ({
          ...filters,
          execution_id,
          offset: 0,
        }))
      }
      onInvocationModeChange={(runtime_mode) =>
        view.setInvocationFilters((filters) => ({
          ...filters,
          offset: 0,
          runtime_mode,
        }))
      }
      onInvocationPluginChange={(plugin_id) =>
        view.setInvocationFilters((filters) => ({
          ...filters,
          offset: 0,
          plugin_id,
        }))
      }
      onInvocationStatusChange={(status) =>
        view.setInvocationFilters((filters) => ({
          ...filters,
          offset: 0,
          status,
        }))
      }
      onRefresh={refreshAll}
      onSelectAccess={(item) => {
        view.setSelectedInvocation(null)
        view.setSelectedAccess(item)
      }}
      onSelectInvocation={(item) => {
        view.setSelectedAccess(null)
        view.setSelectedInvocation(item)
      }}
      onTabChange={view.setActiveTab}
      selectedAccess={view.selectedAccess}
      selectedInvocation={view.selectedInvocation}
    />
  )
}
