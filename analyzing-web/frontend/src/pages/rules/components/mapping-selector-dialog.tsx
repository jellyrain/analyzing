import { useState } from "react"

import { CheckSquare2, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import type { MappingCandidate } from "@/pages/rules/mapping-candidates"

type MappingSelectorDialogProps = {
  candidates: MappingCandidate[]
  onAdd: (candidates: MappingCandidate[]) => void
  onOpenChange: (open: boolean) => void
  open: boolean
}

/** 从真实 parsed 结果中批量选择叶子字段，统一创建字段映射。 */
export function MappingSelectorDialog({ candidates, onAdd, onOpenChange, open }: MappingSelectorDialogProps) {
  const [selectedPaths, setSelectedPaths] = useState<Set<string>>(() => new Set())
  const toggle = (path: string) => {
    setSelectedPaths((current) => {
      const next = new Set(current)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }
  const close = () => {
    setSelectedPaths(new Set())
    onOpenChange(false)
  }
  const submit = () => {
    onAdd(candidates.filter((candidate) => selectedPaths.has(candidate.path)))
    close()
  }
  const allSelected = selectedPaths.size === candidates.length
  const toggleAll = () => {
    setSelectedPaths(
      allSelected ? new Set() : new Set(candidates.map((candidate) => candidate.path))
    )
  }

  return (
    <Dialog onOpenChange={(nextOpen) => { if (!nextOpen) close() }} open={open}>
      <DialogContent className="gap-0 p-0 sm:max-w-2xl" showCloseButton={false}>
        <DialogHeader className="border-b border-border px-5 py-4">
          <DialogTitle className="flex items-center gap-2"><CheckSquare2 className="size-4 text-primary" />选择解析字段</DialogTitle>
          <DialogDescription>候选项来自本次 Engine 解析的 parsed 结果，可一次选择多个字段。</DialogDescription>
        </DialogHeader>
        <div className="max-h-[min(60vh,34rem)] overflow-y-auto px-5 py-4">
          <div className="space-y-1">
            {candidates.map((candidate) => {
              const checked = selectedPaths.has(candidate.path)
              return <label className={`flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 transition-colors ${checked ? "bg-primary/10 text-foreground" : "hover:bg-muted"}`} key={candidate.path}><Checkbox checked={checked} onCheckedChange={() => toggle(candidate.path)} /><span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium">{candidate.alias}</span><span className="mt-0.5 block truncate font-mono text-xs text-muted-foreground">{candidate.path}</span></span><span className="max-w-48 truncate text-xs text-muted-foreground">{candidate.preview}</span></label>
            })}
          </div>
        </div>
        <DialogFooter className="mx-0 mb-0 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3"><span className="text-xs text-muted-foreground">已选择 {selectedPaths.size} 项</span><Button onClick={toggleAll} size="sm" variant="ghost">{allSelected ? "取消全选" : "全选"}</Button></div>
          <div className="flex gap-2"><Button onClick={close} variant="outline">取消</Button><Button disabled={selectedPaths.size === 0} onClick={submit}><Plus />添加字段映射</Button></div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
