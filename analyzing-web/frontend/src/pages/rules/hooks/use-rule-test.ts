import { useState } from "react"

import { useMutation } from "@tanstack/react-query"

import { runProcessor } from "@/api/engine-processor"
import { buildEngineConfig } from "@/pages/rules/build-engine-config"
import type { RuleDraft } from "@/pages/rules/types"

/** 运行当前本地草稿；保存与执行解耦，避免在测试时写入未完成的规则。 */
export function useRuleTest(draft: RuleDraft | null) {
  const [validationError, setValidationError] = useState<string | null>(null)
  const mutation = useMutation({
    mutationFn: ({
      config,
      text,
    }: {
      config: Record<string, unknown>
      text: string
    }) => runProcessor(text, config),
  })

  const run = () => {
    if (!draft) {
      return
    }

    if (!draft.testText.trim()) {
      setValidationError("请先输入需要测试的原始文本")
      return
    }

    try {
      const config = buildEngineConfig(draft)
      setValidationError(null)
      mutation.mutate({ config, text: draft.testText })
    } catch (error) {
      setValidationError(
        error instanceof Error ? error.message : "规则配置无效"
      )
    }
  }

  return {
    error: validationError ?? mutation.error,
    isRunning: mutation.isPending,
    result: mutation.data,
    run,
  }
}
