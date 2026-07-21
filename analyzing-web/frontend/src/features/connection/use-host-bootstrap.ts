import { useQuery } from "@tanstack/react-query"

import { getBootstrap } from "@/api/host"

/** 启动时读取 Host 是否已完成 Engine 连接配置。 */
export function useHostBootstrap() {
  return useQuery({
    queryKey: ["host", "bootstrap"],
    queryFn: getBootstrap,
  })
}
