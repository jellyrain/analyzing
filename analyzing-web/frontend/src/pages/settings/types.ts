import type { HostConfig } from "@/api/host"

export type Feedback = {
  tone: "success" | "error" | "neutral"
  message: string
}

export type HostConfigActions = {
  onRestore: () => void
  onSave: () => void
  onTest: () => void
  onUpdate: (next: Partial<HostConfig>) => void
}
