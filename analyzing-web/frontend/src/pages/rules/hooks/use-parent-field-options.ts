import { useState } from "react"

import { useMutation } from "@tanstack/react-query"

import { runProcessor } from "@/api/engine-processor"
import { buildParentPreviewConfig } from "@/pages/rules/build-engine-config"
import type { RuleDraft } from "@/pages/rules/types"

/** 通过一次父级链路预览解析，提取可作为子节点入口的字段名。 */
export function useParentFieldOptions(draft: RuleDraft, nodeId: string) {
  const [validationError, setValidationError] = useState<string | null>(null)
  const mutation = useMutation({
    mutationFn: ({ config, text }: { config: Record<string, unknown>; text: string }) =>
      runProcessor(text, config),
  })

  const load = () => {
    mutation.reset()
    if (!draft.testText.trim()) {
      setValidationError("请先在右侧规则测试中输入原始文本")
      return
    }
    try {
      setValidationError(null)
      mutation.mutate({
        config: buildParentPreviewConfig(draft, nodeId),
        text: draft.testText,
      })
    } catch (reason) {
      setValidationError(reason instanceof Error ? reason.message : "无法构建父级预览")
    }
  }

  return {
    error: validationError ?? mutation.error,
    fields: collectFields(mutation.data),
    hasSucceeded: mutation.isSuccess,
    isLoading: mutation.isPending,
    load,
  }
}

function collectFields(value: unknown) {
  const fields = new Set<string>()
  if (
    typeof value === "object" &&
    value !== null &&
    "parsed" in value &&
    typeof value.parsed === "object" &&
    value.parsed !== null
  ) {
    collectRecordFields(value.parsed, fields)
  }
  return [...fields].sort((left, right) => left.localeCompare(right, "zh-CN"))
}

function collectRecordFields(value: unknown, fields: Set<string>) {
  if (Array.isArray(value)) {
    value.forEach((item) => collectRecordFields(item, fields))
    return
  }
  if (typeof value !== "object" || value === null) return
  for (const [key, child] of Object.entries(value)) {
    fields.add(key)
    collectRecordFields(child, fields)
  }
}
