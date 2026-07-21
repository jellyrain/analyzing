import type {
  AccessFilters,
  AccessLogRecord,
  InvocationFilters,
  PluginInvocationRecord,
} from "@/api/engine-monitor"

export type MonitorTab = "invocations" | "access"

export type MonitorFilters = {
  access: AccessFilters
  invocations: InvocationFilters
}

export type MonitorSelection = {
  access: AccessLogRecord | null
  invocation: PluginInvocationRecord | null
}
