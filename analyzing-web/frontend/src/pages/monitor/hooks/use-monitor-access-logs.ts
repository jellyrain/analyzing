import { useQuery } from "@tanstack/react-query"

import { getMonitorAccessLogs, type AccessFilters } from "@/api/engine-monitor"

/** 按服务端筛选条件查询 Engine API 访问日志。 */
export function useMonitorAccessLogs(
  filters: AccessFilters,
  enabled: boolean,
  refreshMilliseconds: number
) {
  return useQuery({
    queryKey: ["monitor", "access", filters],
    queryFn: () => getMonitorAccessLogs(filters),
    enabled,
    refetchInterval: enabled ? refreshMilliseconds : false,
    refetchIntervalInBackground: false,
  })
}
