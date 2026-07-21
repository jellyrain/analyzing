import { Check, CircleAlert, Server } from "lucide-react"

import type { Feedback } from "@/pages/settings/types"

type FeedbackLineProps = {
  feedback: Feedback | null
}

/** 表单内联反馈，保留结果上下文，不使用短暂消失的 Toast。 */
export function FeedbackLine({ feedback }: FeedbackLineProps) {
  if (feedback === null) {
    return null
  }

  const isError = feedback.tone === "error"
  const isSuccess = feedback.tone === "success"
  const className = isError
    ? "text-destructive"
    : isSuccess
      ? "text-primary"
      : "text-muted-foreground"

  return (
    <div aria-live="polite" className={`flex items-start gap-2 text-sm leading-6 ${className}`}>
      {isError ? (
        <CircleAlert className="mt-1 size-4 shrink-0" />
      ) : isSuccess ? (
        <Check className="mt-1 size-4 shrink-0" />
      ) : (
        <Server className="mt-1 size-4 shrink-0" />
      )}
      <p>{feedback.message}</p>
    </div>
  )
}
