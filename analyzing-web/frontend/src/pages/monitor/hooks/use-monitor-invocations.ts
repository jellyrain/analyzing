import { useQuery } from "@tanstack/react-query"

import { getMonitorInvocations, type InvocationFilters } from "@/api/engine-monitor"

/** 按服务端筛选条件查询插件调用记录。 */
export function useMonitorInvocations(
  filters: InvocationFilters,
  enabled: boolean,
  refreshMilliseconds: number
) {
  return useQuery({
    queryKey: ["monitor", "invocations", filters],
    queryFn: () => getMonitorInvocations(filters),
    enabled,
    refetchInterval: enabled ? refreshMilliseconds : false,
    refetchIntervalInBackground: false,
  })
}
