import { http } from "@/api/http"
import type { JsonValue } from "@/pages/rules/types"

export type PluginFormOption = {
  label: string
  value: boolean | number | string
}

export type PluginFormField = {
  allow_empty?: boolean
  default?: JsonValue
  items?: PluginFormField
  label: string
  options?: PluginFormOption[]
  placeholder?: string
  properties?: Record<string, PluginFormField>
  required?: boolean
  type: "array" | "boolean" | "integer" | "number" | "object" | "string"
  widget:
    | "checkbox_group"
    | "input"
    | "list"
    | "number"
    | "radio"
    | "select"
    | "switch"
    | "textarea"
}

export type PluginFormSchema = {
  fields?: Record<string, PluginFormField>
  sections?: Array<{ fields: string[]; title: string }>
  version?: number
}

export type CatalogPlugin = {
  form_schema: PluginFormSchema
  name: string
  plugin_id: string
  plugin_role: string
  plugin_type: "parser" | "splitter" | null
  runtime_status: string
  summary: string
}

type EngineResponse<T> = {
  code: number
  message: string
  data: T
}

/** 查询 Engine 已发现插件，供规则编辑器按角色选择并渲染 form.schema.json。 */
export async function getCatalogPlugins() {
  const response =
    await http.get<EngineResponse<{ plugins: CatalogPlugin[] }>>(
      "/engine/plugins"
    )

  if (response.data.code !== 200) {
    throw new Error(response.data.message)
  }

  return response.data.data.plugins
}
