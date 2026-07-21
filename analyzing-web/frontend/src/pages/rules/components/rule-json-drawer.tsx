import { Check, Copy, Upload } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Textarea } from "@/components/ui/textarea"
import type { RuleJsonMode } from "@/pages/rules/hooks/use-rule-json-transfer"

type RuleJsonDrawerProps = {
  error: string | null
  exportText: string
  importText: string
  isImporting: boolean
  mode: RuleJsonMode
  onClose: () => void
  onCopy: () => void
  onImportTextChange: (text: string) => void
  onSubmitImport: () => void
}

/** 以抽屉方式查看或粘贴规则 JSON，不打断当前编辑上下文。 */
export function RuleJsonDrawer({ error, exportText, importText, isImporting, mode, onClose, onCopy, onImportTextChange, onSubmitImport }: RuleJsonDrawerProps) {
  const importing = mode === "import"
  return (
    <Sheet onOpenChange={(open) => { if (!open) onClose() }} open={mode !== null}>
      <SheetContent className="gap-0 p-0 sm:max-w-[42rem]" side="right">
        <SheetHeader className="border-b border-border pr-12">
          <SheetTitle>{importing ? "粘贴 JSON 导入" : "规则 JSON"}</SheetTitle>
          <SheetDescription>{importing ? "仅支持标准 PipelineExtractionConfig，导入后会替换当前规则。" : "这里展示 Engine 可直接使用的 PipelineExtractionConfig，可复制或下载为文件。"}</SheetDescription>
        </SheetHeader>
        <div className="min-h-0 flex-1 px-5 py-5">
          <Label htmlFor="rule-json-text">规则 JSON</Label>
          <Textarea
            className="mt-2 h-full min-h-80 resize-none overflow-auto font-mono text-xs leading-5 [field-sizing:fixed]"
            id="rule-json-text"
            onChange={(event) => onImportTextChange(event.target.value)}
            placeholder="粘贴标准 PipelineExtractionConfig JSON"
            readOnly={!importing}
            value={importing ? importText : exportText}
          />
          {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
        </div>
        <SheetFooter className="border-t border-border sm:flex-row sm:justify-end">
          {importing ? <Button disabled={isImporting || !importText.trim()} onClick={onSubmitImport}><Upload />{isImporting ? "正在导入" : "替换当前规则"}</Button> : <Button disabled={!exportText} onClick={onCopy}><Copy />复制 JSON</Button>}
          <Button onClick={onClose} variant="outline"><Check />完成</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
