/** 规则编辑器当前使用的本地草稿结构，后续可映射到 Engine 的规则 CRUD 模型。 */
export type RuleTab = "split" | "pipeline" | "mapping"

/** 右侧检查器当前选中的可配置节点。 */
export type RuleEditorItem =
  | { id: string; kind: "split" }
  | { id: string; kind: "parser" }

export type JsonValue =
  boolean | number | string | null | JsonValue[] | { [key: string]: JsonValue }

export type SplitStep = {
  id: string
  pluginId: string
  params: Record<string, JsonValue>
}

export type PipelineNode = {
  aliasPrefix: string
  childField: string
  flatten: boolean
  id: string
  parserId: string
  params: Record<string, JsonValue>
  children: PipelineNode[]
}

export type FieldMapping = {
  id: string
  source: string
  target: string
}

export type RuleDraft = {
  id: string
  name: string
  splitSteps: SplitStep[]
  pipelineNodes: PipelineNode[]
  mappings: FieldMapping[]
  testText: string
}
