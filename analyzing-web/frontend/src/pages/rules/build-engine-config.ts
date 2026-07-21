import type { PipelineNode, RuleDraft } from "@/pages/rules/types"

type EngineParserConfig = {
  app_root?: string
  alias_prefix?: string
  children?: Record<string, EngineParserConfig[]>
  flatten: boolean
  parser_params?: Record<string, unknown>
  parser_type: string
}

const virtualRootChildKey = "re"
const virtualRootPattern = "([\\s\\S]+)"

function buildParserNode(node: PipelineNode, path: string): EngineParserConfig {
  if (!node.parserId.trim()) {
    throw new Error(`${path} 缺少解析器插件 ID`)
  }

  const childGroups: Record<string, EngineParserConfig[]> = {}

  for (const [index, child] of node.children.entries()) {
    if (!child.childField.trim()) {
      throw new Error(`${path}.children[${index}] 缺少父级字段名`)
    }

    const group = childGroups[child.childField] ?? []
    group.push(
      buildParserNode(child, `${path}.${child.childField}[${group.length}]`)
    )
    childGroups[child.childField] = group
  }

  return {
    ...(node.aliasPrefix.trim()
      ? { alias_prefix: node.aliasPrefix.trim() }
      : {}),
    ...(Object.keys(childGroups).length > 0 ? { children: childGroups } : {}),
    flatten: node.flatten,
    ...(Object.keys(node.params).length > 0
      ? { parser_params: node.params }
      : {}),
    parser_type: node.parserId.trim(),
  }
}

/** 多个可视根节点通过与旧版一致的正则虚拟根包装为 Engine 的单根配置。 */
function buildRootParserConfig(nodes: PipelineNode[]) {
  if (nodes.length === 0) {
    throw new Error("解析流水线至少需要一个根节点")
  }
  if (nodes.length === 1) {
    return buildParserNode(nodes[0], "parser_config")
  }
  return {
    app_root: "re",
    children: {
      [virtualRootChildKey]: nodes.map((node, index) =>
        buildParserNode(node, `parser_config.children.re[${index}]`)
      ),
    },
    flatten: true,
    parser_params: {
      group_index: 1,
      negative_pattern: "",
      pattern: virtualRootPattern,
    },
    parser_type: "re",
  }
}

/** 将本地编辑草稿转换为 Engine `/processor` 所需的合法配置对象。 */
export function buildEngineConfig(draft: RuleDraft) {
  if (!draft.name.trim()) {
    throw new Error("请填写规则名称")
  }

  const splitConfig = draft.splitSteps.map((step, index) => {
    if (!step.pluginId.trim()) {
      throw new Error(`切分步骤 ${index + 1} 缺少切分器插件 ID`)
    }

    return {
      ...(Object.keys(step.params).length > 0
        ? { split_params: step.params }
        : {}),
      split_type: step.pluginId.trim(),
    }
  })

  const fieldMapping: Record<string, string> = {}
  for (const [index, mapping] of draft.mappings.entries()) {
    if (!mapping.target.trim() || !mapping.source.trim()) {
      throw new Error(`字段映射 ${index + 1} 必须同时填写来源字段和目标字段`)
    }
    if (!mapping.source.trim().startsWith("$")) {
      throw new Error(`字段映射 ${index + 1} 的来源字段必须以 $ 开头`)
    }
    fieldMapping[mapping.target.trim()] = mapping.source.trim()
  }

  return {
    extraction_id: draft.id,
    extraction_name: draft.name.trim(),
    ...(fieldMapping && Object.keys(fieldMapping).length > 0
      ? { field_mapping: fieldMapping }
      : {}),
    parser_config: buildRootParserConfig(draft.pipelineNodes),
    split_config: splitConfig.length > 0 ? splitConfig : null,
  }
}

/** 构建选中子节点的父级预览配置，用于从真实解析结果中选择父级字段。 */
export function buildParentPreviewConfig(draft: RuleDraft, nodeId: string) {
  const path = findNodePath(draft.pipelineNodes, nodeId)
  if (!path || path.length < 2) {
    throw new Error("根解析节点不需要选择父级字段")
  }
  const parentPath = path.slice(0, -1)
  const previewRoot = cloneNodePath(parentPath, 0)
  return {
    extraction_id: draft.id,
    extraction_name: draft.name.trim() || "父级字段预览",
    parser_config: buildParserNode(previewRoot, "parser_config"),
    // 仅保留已配置的切分步骤，未完成的其他编辑不应阻止父级字段预览请求。
    split_config: draft.splitSteps
      .filter((step) => step.pluginId.trim())
      .map((step) => ({
        ...(Object.keys(step.params).length > 0
          ? { split_params: step.params }
          : {}),
        split_type: step.pluginId.trim(),
      })),
  }
}

function findNodePath(nodes: PipelineNode[], nodeId: string): PipelineNode[] | null {
  for (const node of nodes) {
    if (node.id === nodeId) return [node]
    const childPath = findNodePath(node.children, nodeId)
    if (childPath) return [node, ...childPath]
  }
  return null
}

function cloneNodePath(path: PipelineNode[], index: number): PipelineNode {
  const node = path[index]
  return {
    ...node,
    children: index === path.length - 1 ? [] : [cloneNodePath(path, index + 1)],
  }
}
