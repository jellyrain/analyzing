import { FlaskConical } from "lucide-react"

import { ScrollArea } from "@/components/ui/scroll-area"
import { RuleTestPanel } from "@/pages/rules/components/rule-test-panel"
import type { RuleDraft } from "@/pages/rules/types"

type RuleInspectorProps = {
  draft: RuleDraft | null
  onUpdateTestText: (text: string) => void
}

/** 右侧固定保留规则测试，节点配置通过独立抽屉按需打开。 */
export function RuleInspector({ draft, onUpdateTestText }: RuleInspectorProps) {
  return (
    <aside className="flex min-h-0 flex-col border-l border-border bg-sidebar/28">
      <header className="border-b border-border px-4 py-4">
        <p className="text-xs font-semibold tracking-[0.14em] text-primary">
          RULE TEST
        </p>
        <h2 className="mt-1 flex items-center gap-2 text-sm font-semibold">
          <FlaskConical className="size-4 text-primary" />
          规则测试
        </h2>
      </header>
      <ScrollArea className="min-h-0 flex-1">
        <div className="px-4 py-5">
          <RuleTestPanel draft={draft} onUpdateTestText={onUpdateTestText} />
        </div>
      </ScrollArea>
    </aside>
  )
}
