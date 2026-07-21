import { useState } from "react"

import type { PluginStatusRecord } from "@/api/engine-monitor"

/** 管理插件状态页当前展开的插件详情。 */
export function usePluginHealthView() {
  const [selectedPlugin, setSelectedPlugin] = useState<PluginStatusRecord | null>(null)

  return {
    selectedPlugin,
    setSelectedPlugin,
  }
}
