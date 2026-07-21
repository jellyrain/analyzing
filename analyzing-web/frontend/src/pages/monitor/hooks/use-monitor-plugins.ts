import { useQuery } from "@tanstack/react-query"

import { getMonitorPlugins } from "@/api/engine-monitor"

/** 查询插件当前运行状态快照。 */
export function useMonitorPlugins(enabled: boolean, refreshMilliseconds: number) {
  return useQuery({
    queryKey: ["monitor", "plugins"],
    queryFn: getMonitorPlugins,
    enabled,
    refetchInterval: enabled ? refreshMilliseconds : false,
    refetchIntervalInBackground: false,
  })
}
