import { Download, Save, Upload } from "lucide-react"

import { Button } from "@/components/ui/button"
import { RuleJsonDrawer } from "@/pages/rules/components/rule-json-drawer"
import { useRuleJsonTransfer } from "@/pages/rules/hooks/use-rule-json-transfer"
import { serializeRuleDraft } from "@/pages/rules/rule-draft-storage"
import type { RuleDraft } from "@/pages/rules/types"

type RuleActionsProps = {
  draft: RuleDraft
  onExportFile: () => void
  onImportFile: (file: File) => Promise<void>
  onImportText: (text: string) => Promise<void>
  onSave: () => void
}

/** 规则保存、导入和 JSON 获取操作，统一放在编辑器标题栏。 */
export function RuleActions({ draft, onExportFile, onImportFile, onImportText, onSave }: RuleActionsProps) {
  const {
    close,
    error,
    fileInputRef,
    importFile,
    importText,
    isImporting,
    mode,
    openExport,
    openImport,
    setImportText,
    submitTextImport,
  } = useRuleJsonTransfer({ onImportFile, onImportText })
  let exportText = ""
  let exportError: string | null = null
  try {
    exportText = serializeRuleDraft(draft)
  } catch (reason) {
    exportError = reason instanceof Error ? reason.message : "无法生成规则 JSON"
  }

  return (
    <div className="flex items-center gap-1">
      <input accept="application/json,.json" className="sr-only" onChange={(event) => { const file = event.target.files?.[0]; event.target.value = ""; if (file) importFile(file) }} ref={fileInputRef} type="file" />
      <Button onClick={() => fileInputRef.current?.click()} size="sm" title="从 JSON 文件替换当前规则" variant="ghost"><Upload />导入文件</Button>
      <Button onClick={openImport} size="sm" title="粘贴 JSON 替换当前规则" variant="ghost"><Upload />粘贴 JSON</Button>
      <Button onClick={openExport} size="sm" title="查看并复制当前 Engine 规则 JSON" variant="ghost"><Download />获取 JSON</Button>
      <Button onClick={() => { if (exportError) { window.alert(exportError); return }; onExportFile() }} size="sm" title="下载当前 Engine 规则 JSON 文件" variant="ghost"><Download />下载文件</Button>
      <Button onClick={onSave} size="sm" title="保存全部规则到当前浏览器" variant="outline"><Save />保存</Button>
      <RuleJsonDrawer
        error={mode === "export" ? exportError : error}
        exportText={exportText}
        importText={importText}
        isImporting={isImporting}
        mode={mode}
        onClose={close}
        onCopy={() => void navigator.clipboard.writeText(exportText)}
        onImportTextChange={setImportText}
        onSubmitImport={() => void submitTextImport()}
      />
    </div>
  )
}
