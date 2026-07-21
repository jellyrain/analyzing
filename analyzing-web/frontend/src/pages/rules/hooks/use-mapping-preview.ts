import { useState } from "react"

import { useMutation } from "@tanstack/react-query"

import { runProcessor } from "@/api/engine-processor"
import { buildEngineConfig } from "@/pages/rules/build-engine-config"
import { buildMappingCandidates, type MappingCandidate } from "@/pages/rules/mapping-candidates"
import type { RuleDraft } from "@/pages/rules/types"

export type MappingPreviewState = {
  candidates: MappingCandidate[]
  error: Error | null
  isLoading: boolean
  isReady: boolean
  run: () => void
}

/** 字段映射进入时执行一次预览解析，映射候选只来自本次真实 parsed 结果。 */
export function useMappingPreview(draft: RuleDraft | null): MappingPreviewState {
  const [validationError, setValidationError] = useState<Error | null>(null)
  const mutation = useMutation({
    mutationFn: ({ config, text }: { config: Record<string, unknown>; text: string }) =>
      runProcessor(text, config),
  })

  const run = () => {
    mutation.reset()
    if (!draft) return
    if (!draft.testText.trim()) {
      setValidationError(new Error("请先在右侧规则测试中输入原始文本"))
      return
    }
    try {
      setValidationError(null)
      mutation.mutate({
        config: buildEngineConfig({ ...draft, mappings: [] }),
        text: draft.testText,
      })
    } catch (reason) {
      setValidationError(
        reason instanceof Error ? reason : new Error("无法构建字段映射预览")
      )
    }
  }

  const parsed = getParsed(mutation.data)
  const error = validationError ?? toError(mutation.error)
  return {
    candidates: mutation.isSuccess ? buildMappingCandidates(parsed) : [],
    error,
    isLoading: mutation.isPending,
    isReady: mutation.isSuccess,
    run,
  }
}

function getParsed(value: unknown) {
  if (
    typeof value === "object" &&
    value !== null &&
    "parsed" in value &&
    typeof value.parsed === "object" &&
    value.parsed !== null
  ) {
    return value.parsed
  }
  return {}
}

function toError(value: unknown) {
  return value instanceof Error ? value : null
}
