import type { JsonValue, PipelineNode, RuleDraft } from "@/pages/rules/types"
import { buildEngineConfig } from "@/pages/rules/build-engine-config"

const storageKey = "analyzing-web.rule-drafts.v1"

/** 从浏览器本地存储读取规则草稿；损坏数据不影响打开编辑器。 */
export function loadLocalRuleDrafts(): RuleDraft[] {
  try {
    const raw = window.localStorage.getItem(storageKey)
    if (!raw) return []
    const value = JSON.parse(raw) as unknown
    return Array.isArray(value) ? value.map(toRuleDraft) : []
  } catch {
    return []
  }
}

/** 将当前全部草稿写入浏览器本地存储，后续可在此增加 Engine 同步。 */
export function saveLocalRuleDrafts(drafts: RuleDraft[]) {
  window.localStorage.setItem(storageKey, JSON.stringify(drafts))
}

/** 生成 Engine 可直接读取的单规则 JSON 文件。 */
export function downloadRuleDraft(draft: RuleDraft) {
  const blob = new Blob([serializeRuleDraft(draft)], {
    type: "application/json",
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = `${safeFileName(draft.name || "未命名规则")}.json`
  anchor.click()
  URL.revokeObjectURL(url)
}

/** 读取并校验导入的 Engine PipelineExtractionConfig 文件。 */
export async function readRuleDraftFile(file: File) {
  return readRuleDraftText(await file.text())
}

/** 将当前规则转为 Engine 可直接使用的 JSON 文本。 */
export function serializeRuleDraft(draft: RuleDraft) {
  return JSON.stringify(buildEngineConfig(draft), null, 2)
}

/** 读取并校验用户粘贴的 Engine PipelineExtractionConfig 文本。 */
export function readRuleDraftText(text: string) {
  const value = JSON.parse(text) as unknown
  if (!isRecord(value)) {
    throw new Error("规则 JSON 格式不正确")
  }
  if ("parser_config" in value && "extraction_name" in value) {
    return fromEngineConfig(value)
  }
  throw new Error("JSON 必须是标准的 PipelineExtractionConfig")
}

/** 将 Engine PipelineExtractionConfig 还原为编辑器可操作的规则草稿。 */
function fromEngineConfig(value: Record<string, unknown>): RuleDraft {
  const splitConfig = value.split_config
  const mapping = value.field_mapping
  return {
    id: stringValue(value.extraction_id, "规则 ID"),
    mappings: mapping === undefined ? [] : toEngineMappings(mapping),
    name: stringValue(value.extraction_name, "规则名称"),
    pipelineNodes: unwrapEngineRootNodes(
      recordValue(value.parser_config, "解析配置")
    ),
    splitSteps:
      splitConfig === null || splitConfig === undefined
        ? []
        : arrayValue(splitConfig, "切分配置").map(toEngineSplitStep),
    testText: "",
  }
}

/** 识别旧版同款虚拟根，导入时恢复为多个可视根节点。 */
function unwrapEngineRootNodes(config: Record<string, unknown>): PipelineNode[] {
  const children = config.children
  if (
    config.app_root === "re" &&
    config.parser_type === "re" &&
    config.flatten === true &&
    isRecord(children) &&
    Array.isArray(children.re)
  ) {
    return children.re.map((node) =>
      toEngineNode(recordValue(node, "虚拟根子节点"), "")
    )
  }
  return [toEngineNode(config, "")]
}

function toEngineSplitStep(value: unknown) {
  const config = recordValue(value, "切分配置")
  return {
    id: crypto.randomUUID(),
    params:
      config.split_params === undefined
        ? {}
        : jsonRecord(config.split_params, "切分参数"),
    pluginId: stringValue(config.split_type, "切分器插件 ID"),
  }
}

function toEngineNode(value: Record<string, unknown>, childField: string): PipelineNode {
  const childrenConfig = value.children
  const children: PipelineNode[] = []
  if (childrenConfig !== undefined) {
    for (const [field, nodes] of Object.entries(
      recordValue(childrenConfig, "子节点配置")
    )) {
      for (const node of arrayValue(nodes, `子节点 ${field}`)) {
        children.push(toEngineNode(recordValue(node, `子节点 ${field}`), field))
      }
    }
  }
  return {
    aliasPrefix:
      value.alias_prefix === undefined
        ? ""
        : stringValue(value.alias_prefix, "拍平别名前缀"),
    childField,
    children,
    flatten:
      value.flatten === undefined
        ? false
        : booleanValue(value.flatten, "拍平开关"),
    id: crypto.randomUUID(),
    params:
      value.parser_params === undefined
        ? {}
        : jsonRecord(value.parser_params, "解析参数"),
    parserId: stringValue(value.parser_type, "解析器插件 ID"),
  }
}

function toEngineMappings(value: unknown) {
  return Object.entries(recordValue(value, "字段映射")).map(([target, source]) => ({
    id: crypto.randomUUID(),
    source: stringValue(source, `字段映射 ${target}`),
    target,
  }))
}

function toRuleDraft(value: unknown): RuleDraft {
  if (!isRecord(value)) throw new Error("规则 JSON 格式不正确")
  return {
    id: stringValue(value.id, "规则 ID"),
    mappings: arrayValue(value.mappings, "字段映射").map(toMapping),
    name: stringValue(value.name, "规则名称"),
    pipelineNodes: arrayValue(value.pipelineNodes, "解析节点").map(toPipelineNode),
    splitSteps: arrayValue(value.splitSteps, "切分步骤").map(toSplitStep),
    testText: typeof value.testText === "string" ? value.testText : "",
  }
}

function toSplitStep(value: unknown) {
  if (!isRecord(value)) throw new Error("切分步骤格式不正确")
  return {
    id: stringValue(value.id, "切分步骤 ID"),
    params: jsonRecord(value.params, "切分参数"),
    pluginId: stringValue(value.pluginId, "切分器插件 ID"),
  }
}

function toPipelineNode(value: unknown): PipelineNode {
  if (!isRecord(value)) throw new Error("解析节点格式不正确")
  return {
    aliasPrefix: stringValue(value.aliasPrefix, "别名前缀"),
    childField: stringValue(value.childField, "父级字段名"),
    children: arrayValue(value.children, "子节点").map(toPipelineNode),
    flatten: booleanValue(value.flatten, "拍平开关"),
    id: stringValue(value.id, "解析节点 ID"),
    params: jsonRecord(value.params, "解析参数"),
    parserId: stringValue(value.parserId, "解析器插件 ID"),
  }
}

function toMapping(value: unknown) {
  if (!isRecord(value)) throw new Error("字段映射格式不正确")
  return {
    id: stringValue(value.id, "字段映射 ID"),
    source: stringValue(value.source, "来源字段"),
    target: stringValue(value.target, "目标字段"),
  }
}

function jsonRecord(value: unknown, fieldName: string): Record<string, JsonValue> {
  if (!isRecord(value)) throw new Error(`${fieldName}格式不正确`)
  return value as Record<string, JsonValue>
}

function recordValue(value: unknown, fieldName: string): Record<string, unknown> {
  if (!isRecord(value)) throw new Error(`${fieldName}格式不正确`)
  return value
}

function stringValue(value: unknown, fieldName: string) {
  if (typeof value !== "string") throw new Error(`${fieldName}格式不正确`)
  return value
}

function booleanValue(value: unknown, fieldName: string) {
  if (typeof value !== "boolean") throw new Error(`${fieldName}格式不正确`)
  return value
}

function arrayValue(value: unknown, fieldName: string) {
  if (!Array.isArray(value)) throw new Error(`${fieldName}格式不正确`)
  return value
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function safeFileName(name: string) {
  return name.replace(/[\\/:*?"<>|]/g, "_")
}
