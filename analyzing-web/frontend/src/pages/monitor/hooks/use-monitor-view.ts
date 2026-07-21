import { useState } from "react"

import type {
  AccessFilters,
  InvocationFilters,
  PluginInvocationRecord,
} from "@/api/engine-monitor"
import type { AccessLogRecord } from "@/api/engine-monitor"
import type { MonitorTab } from "@/pages/monitor/types"

/** 管理监控页的本地筛选、Tab 与当前详情选择。 */
export function useMonitorView() {
  const [activeTab, setActiveTab] = useState<MonitorTab>("invocations")
  const [invocationFilters, setInvocationFilters] = useState<InvocationFilters>({
    offset: 0,
    limit: 50,
  })
  const [accessFilters, setAccessFilters] = useState<AccessFilters>({
    offset: 0,
    limit: 50,
  })
  const [selectedInvocation, setSelectedInvocation] =
    useState<PluginInvocationRecord | null>(null)
  const [selectedAccess, setSelectedAccess] = useState<AccessLogRecord | null>(null)

  return {
    accessFilters,
    activeTab,
    invocationFilters,
    selectedAccess,
    selectedInvocation,
    setAccessFilters,
    setActiveTab,
    setInvocationFilters,
    setSelectedAccess,
    setSelectedInvocation,
  }
}
