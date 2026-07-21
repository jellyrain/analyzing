import { useQuery } from "@tanstack/react-query"

import { getCatalogPlugins } from "@/api/engine-plugins"

/** 加载规则编辑所需的 splitter 和 parser 插件目录。 */
export function useCatalogPlugins(enabled: boolean) {
  return useQuery({
    queryKey: ["plugins", "catalog"],
    queryFn: getCatalogPlugins,
    enabled,
    staleTime: 30_000,
  })
}
