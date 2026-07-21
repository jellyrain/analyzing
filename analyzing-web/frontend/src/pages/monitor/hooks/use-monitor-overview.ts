import { useQuery } from "@tanstack/react-query"

import { getMonitorOverview } from "@/api/engine-monitor"

/** 查询 Engine 当前总览快照。 */
export function useMonitorOverview(enabled: boolean, refreshMilliseconds: number) {
  return useQuery({
    queryKey: ["monitor", "overview"],
    queryFn: getMonitorOverview,
    enabled,
    refetchInterval: enabled ? refreshMilliseconds : false,
    refetchIntervalInBackground: false,
  })
}
