import { RefreshCw } from "lucide-react"

import { getApiErrorMessage } from "@/api/http"
import { Button } from "@/components/ui/button"
import { formatDateTime } from "@/lib/format"
import { PluginStatusSummary } from "@/pages/monitor/components/plugin-status-summary"
import { useMonitorOverview } from "@/pages/monitor/hooks/use-monitor-overview"
import { useMonitorPlugins } from "@/pages/monitor/hooks/use-monitor-plugins"
import { useMonitorRefreshInterval } from "@/pages/monitor/hooks/use-monitor-refresh-interval"

/** Engine 与主机快照的独立总览页面。 */
export function MonitorOverviewPage() {
  const { refreshMilliseconds, refreshSeconds } =
    useMonitorRefreshInterval(true)
  const overviewQuery = useMonitorOverview(true, refreshMilliseconds)
  const pluginsQuery = useMonitorPlugins(true, refreshMilliseconds)
  const overview = overviewQuery.data
  const system = overview?.system.latest_system
  const host = overview?.system.latest_host

  return (
    <section>
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.14em] text-primary">
            ENGINE SNAPSHOT
          </p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.02em]">
            运行总览
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Engine 的最新系统与主机采样快照。
          </p>
        </div>
        <Button
          onClick={() =>
            void Promise.all([overviewQuery.refetch(), pluginsQuery.refetch()])
          }
          variant="outline"
        >
          <RefreshCw />
          刷新快照
        </Button>
      </header>
      <div className="mt-6">
        <PluginStatusSummary items={pluginsQuery.data?.items ?? []} />
      </div>
      <p className="mt-3 text-right text-xs text-muted-foreground">
        LIVE / {refreshSeconds}s
      </p>
      {overviewQuery.isError ? (
        <p className="mt-6 text-sm text-destructive">
          {getApiErrorMessage(
            overviewQuery.error,
            "无法读取 Engine 运行快照。"
          )}
        </p>
      ) : null}
      {pluginsQuery.isError ? (
        <p className="mt-3 text-sm text-destructive">
          {getApiErrorMessage(pluginsQuery.error, "无法读取插件状态。")}
        </p>
      ) : null}
      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <section className="border-t border-border pt-5">
          <p className="text-xs font-semibold tracking-[0.14em] text-primary">
            ENGINE
          </p>
          <dl className="mt-4 divide-y divide-border text-sm">
            <div className="flex justify-between py-3">
              <dt className="text-muted-foreground">快照时间</dt>
              <dd>{formatDateTime(system?.created_at)}</dd>
            </div>
            <div className="flex justify-between py-3">
              <dt className="text-muted-foreground">运行中的执行</dt>
              <dd>{system?.running_execution_count ?? "--"}</dd>
            </div>
            <div className="flex justify-between py-3">
              <dt className="text-muted-foreground">异常插件</dt>
              <dd>{system?.error_plugin_count ?? "--"}</dd>
            </div>
          </dl>
        </section>
        <section className="border-t border-border pt-5">
          <p className="text-xs font-semibold tracking-[0.14em] text-primary">
            HOST MACHINE
          </p>
          <dl className="mt-4 divide-y divide-border text-sm">
            <div className="flex justify-between py-3">
              <dt className="text-muted-foreground">快照时间</dt>
              <dd>{formatDateTime(host?.created_at)}</dd>
            </div>
            <div className="flex justify-between py-3">
              <dt className="text-muted-foreground">CPU</dt>
              <dd>{host?.cpu_percent ?? "--"}%</dd>
            </div>
            <div className="flex justify-between py-3">
              <dt className="text-muted-foreground">内存</dt>
              <dd>{host?.memory_percent ?? "--"}%</dd>
            </div>
            <div className="flex justify-between py-3">
              <dt className="text-muted-foreground">磁盘</dt>
              <dd>{host?.disk_percent ?? "--"}%</dd>
            </div>
          </dl>
        </section>
      </div>
    </section>
  )
}
