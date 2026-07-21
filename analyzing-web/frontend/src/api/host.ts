import { http } from "@/api/http"

export type HostConfig = {
  engine_origin: string
  monitor_refresh_seconds: number
}

export type BootstrapResponse = {
  configured: boolean
  engine_origin: string | null
}

export type ConnectionTestResponse = {
  ok: boolean
  engine_origin: string
  status_code: number | null
  message: string
}

export async function getBootstrap(): Promise<BootstrapResponse> {
  const response = await http.get<BootstrapResponse>("/host/bootstrap")
  return response.data
}

export async function getHostConfig(): Promise<HostConfig> {
  const response = await http.get<HostConfig>("/host/config")
  return response.data
}

export async function saveHostConfig(config: HostConfig): Promise<HostConfig> {
  const response = await http.put<HostConfig>("/host/config", config)
  return response.data
}

export async function testHostConfig(
  config: HostConfig
): Promise<ConnectionTestResponse> {
  const response = await http.post<ConnectionTestResponse>(
    "/host/config/test",
    config
  )
  return response.data
}
