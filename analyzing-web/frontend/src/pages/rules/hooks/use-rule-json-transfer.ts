import { useRef, useState } from "react"

export type RuleJsonMode = "export" | "import" | null

/** 管理规则 JSON 的文件导入、文本导入和抽屉状态。 */
export function useRuleJsonTransfer({
  onImportFile,
  onImportText,
}: {
  onImportFile: (file: File) => Promise<void>
  onImportText: (text: string) => Promise<void>
}) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [mode, setMode] = useState<RuleJsonMode>(null)
  const [importText, setImportText] = useState("")
  const [isImporting, setIsImporting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const close = () => {
    setError(null)
    setImportText("")
    setMode(null)
  }

  const importFile = (file: File) => {
    void onImportFile(file).catch((reason: unknown) => {
      window.alert(reason instanceof Error ? reason.message : "导入规则失败")
    })
  }

  const submitTextImport = async () => {
    setError(null)
    setIsImporting(true)
    try {
      await onImportText(importText)
      close()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "导入规则失败")
    } finally {
      setIsImporting(false)
    }
  }

  return {
    close,
    error,
    fileInputRef,
    importFile,
    importText,
    isImporting,
    mode,
    openExport: () => setMode("export"),
    openImport: () => setMode("import"),
    setImportText,
    submitTextImport,
  }
}
