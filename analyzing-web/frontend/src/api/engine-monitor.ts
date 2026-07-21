import { http } from "@/api/http"

export type InvocationStatus =
  "created" | "running" | "succeeded" | "failed" | "timeout" | "skipped"

export type RuntimeMode = "inproc" | "subprocess" | "remote"
export type RuntimeStatus =
  "registered" | "loaded" | "ready" | "unavailable" | "error"
export type InstallStatus = "discovered" | "installed" | "failed" | "removed"

export type PluginInvocationRecord = {
  invocation_id: string
  execution_id: string
  plugin_id: string
  version: string | null
  runtime_mode: RuntimeMode
  status: InvocationStatus
  started_at: string
  finished_at: string | null
  latency_ms: number | null
  input_size: number | null
  output_count: number | null
  error_message: string | null
  detail: {
    operation?: string
    trace_id?: string
    [key: string]: unknown
  }
}

export type PluginStatusRecord = {
  plugin_id: string
  version: string | null
  install_status: InstallStatus
  runtime_status: RuntimeStatus
  updated_at: string
  detail: {
    runtime_mode?: RuntimeMode
    error_message?: string
    plugin_role?: string
    [key: string]: unknown
  }
}

/** Engine 插件详情接口返回的完整登记信息。 */
export type PluginDetail = {
  plugin_id: string
  name: string
  version: string
  plugin_role: string
  infra_slot: string | null
  plugin_type: string | null
  runtime_mode: RuntimeMode
  enabled: boolean
  install_status: InstallStatus
  runtime_status: RuntimeStatus
  summary: string
  description: string
  capabilities: Record<string, unknown>
  form_schema: Record<string, unknown>
  load_strategy: string
  plugin_dir: string
  manifest_file: string | null
  is_compatible: boolean
  error_message: string | null
  manifest: Record<string, unknown> | null
}

export type AccessLogRecord = {
  access_id: string
  trace_id: string | null
  method: string
  path: string
  status_code: number
  request_size: number | null
  response_size: number | null
  latency_ms: number | null
  client_ip: string | null
  detail: Record<string, unknown>
  created_at: string
}

export type SystemSnapshotRecord = {
  snapshot_id: string
  plugin_count: number | null
  ready_plugin_count: number | null
  error_plugin_count: number | null
  running_execution_count: number | null
  detail: Record<string, unknown>
  created_at: string
}

export type HostSnapshotRecord = {
  snapshot_id: string
  cpu_percent: number | null
  memory_percent: number | null
  disk_percent: number | null
  detail: Record<string, unknown>
  created_at: string
}

export type MonitorOverview = {
  system: {
    latest_system: SystemSnapshotRecord | null
    latest_host: HostSnapshotRecord | null
  }
  plugins: {
    count: number
    ready_count: number
    error_count: number
    items: PluginStatusRecord[]
  }
  invocations: {
    recent: PluginInvocationRecord[]
  }
  access: {
    supported: boolean
    message?: string
  }
}

export type InvocationFilters = {
  execution_id?: string
  plugin_id?: string
  status?: InvocationStatus
  runtime_mode?: RuntimeMode
  offset?: number
  limit?: number
}

export type AccessFilters = {
  method?: string
  path?: string
  status_code?: number
  trace_id?: string
  offset?: number
  limit?: number
}

type EngineResponse<T> = {
  code: number
  message: string
  data: T
}

function createSearchParams(
  filters: Record<string, string | number | undefined>
) {
  const searchParams = new URLSearchParams()

  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== "") {
      searchParams.set(key, String(value))
    }
  }

  return searchParams
}

async function getEngineData<T>(path: string, searchParams?: URLSearchParams) {
  const response = await http.get<EngineResponse<T>>(path, {
    params: searchParams,
  })

  if (response.data.code !== 200) {
    throw new Error(response.data.message)
  }

  return response.data.data
}

export function getMonitorOverview() {
  return getEngineData<MonitorOverview>("/engine/monitor/overview")
}

export function getMonitorInvocations(filters: InvocationFilters) {
  return getEngineData<{ items: PluginInvocationRecord[] }>(
    "/engine/monitor/invocations",
    createSearchParams(filters)
  )
}

export function getMonitorPlugins() {
  return getEngineData<{ items: PluginStatusRecord[] }>(
    "/engine/monitor/plugins",
    createSearchParams({ offset: 0, limit: 200 })
  )
}

/** 查询单个插件的完整注册信息，不使用监控快照替代详情。 */
export async function getPluginDetail(pluginId: string) {
  const data = await getEngineData<{ plugin: PluginDetail }>(
    `/engine/plugins/${encodeURIComponent(pluginId)}`
  )

  return data.plugin
}

export function getMonitorAccessLogs(filters: AccessFilters) {
  return getEngineData<{ items: AccessLogRecord[] }>(
    "/engine/monitor/access",
    createSearchParams(filters)
  )
}
