import { RefreshCw } from "lucide-react"

import { getApiErrorMessage } from "@/api/http"
import { Button } from "@/components/ui/button"
import { PluginDetailSheet } from "@/pages/monitor/components/plugin-detail-sheet"
import { PluginHealth } from "@/pages/monitor/components/plugin-health"
import { useMonitorPlugins } from "@/pages/monitor/hooks/use-monitor-plugins"
import { useMonitorRefreshInterval } from "@/pages/monitor/hooks/use-monitor-refresh-interval"
import { usePluginDetail } from "@/pages/monitor/hooks/use-plugin-detail"
import { usePluginHealthView } from "@/pages/monitor/hooks/use-plugin-health-view"

/** 插件当前状态子页面，支持点击查看单个插件详情。 */
export function MonitorPluginsPage() {
  const { refreshMilliseconds } = useMonitorRefreshInterval(true)
  const pluginsQuery = useMonitorPlugins(true, refreshMilliseconds)
  const { selectedPlugin, setSelectedPlugin } = usePluginHealthView()
  const pluginDetailQuery = usePluginDetail(selectedPlugin?.plugin_id)

  return (
    <section className="pt-7">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.14em] text-primary">
            PLUGIN HEALTH
          </p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.02em]">
            插件运行状态
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            点击插件查看安装、运行模式、错误信息和原始状态详情。
          </p>
        </div>
        <Button onClick={() => void pluginsQuery.refetch()} variant="outline">
          <RefreshCw />
          刷新状态
        </Button>
      </header>
      {pluginsQuery.isError ? (
        <p className="mt-6 text-sm text-destructive">
          {getApiErrorMessage(pluginsQuery.error, "无法读取插件状态。")}
        </p>
      ) : (
        <div className="mt-6">
          <PluginHealth
            items={pluginsQuery.data?.items ?? []}
            onSelect={setSelectedPlugin}
          />
        </div>
      )}
      <PluginDetailSheet
        detail={pluginDetailQuery.data}
        error={
          pluginDetailQuery.isError
            ? getApiErrorMessage(
                pluginDetailQuery.error,
                "无法读取插件完整详情。"
              )
            : null
        }
        isLoading={pluginDetailQuery.isPending}
        onOpenChange={(open) => {
          if (!open) setSelectedPlugin(null)
        }}
        plugin={selectedPlugin}
      />
    </section>
  )
}
