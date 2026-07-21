import { useQuery } from "@tanstack/react-query"

import { getPluginDetail } from "@/api/engine-monitor"

/** 仅在用户打开抽屉后请求插件明细，避免列表轮询携带大量 manifest。 */
export function usePluginDetail(pluginId: string | undefined) {
  return useQuery({
    queryKey: ["plugins", "detail", pluginId],
    queryFn: () => getPluginDetail(pluginId!),
    enabled: Boolean(pluginId),
  })
}
