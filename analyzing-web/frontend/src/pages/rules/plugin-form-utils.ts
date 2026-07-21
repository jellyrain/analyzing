import type { PluginFormSchema } from "@/api/engine-plugins"
import type { JsonValue } from "@/pages/rules/types"

/** 选择插件时提取 schema 声明的默认参数值。 */
export function getDefaultParams(schema: PluginFormSchema) {
  return Object.fromEntries(
    Object.entries(schema?.fields ?? {}).flatMap(([fieldId, field]) =>
      field.default === undefined ? [] : [[fieldId, field.default]]
    )
  ) as Record<string, JsonValue>
}
