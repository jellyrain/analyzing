import { useQuery } from "@tanstack/react-query"

import { getHostConfig } from "@/api/host"

/** 读取 Host 配置的监控刷新间隔，所有监控子页共用。 */
export function useMonitorRefreshInterval(enabled: boolean) {
  const hostConfigQuery = useQuery({
    queryKey: ["host", "config"],
    queryFn: getHostConfig,
    enabled,
  })

  const refreshSeconds = hostConfigQuery.data?.monitor_refresh_seconds ?? 5

  return {
    refreshMilliseconds: refreshSeconds * 1_000,
    refreshSeconds,
  }
}
