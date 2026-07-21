import { FlaskConical, Play } from "lucide-react"

import { getApiErrorMessage } from "@/api/http"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useRuleTest } from "@/pages/rules/hooks/use-rule-test"
import type { RuleDraft } from "@/pages/rules/types"

type RuleTestPanelProps = {
  draft: RuleDraft | null
  onUpdateTestText: (text: string) => void
}

/** 规则测试直接调用 Engine processor，执行当前本地草稿而不写入规则库。 */
export function RuleTestPanel({ draft, onUpdateTestText }: RuleTestPanelProps) {
  const test = useRuleTest(draft)

  if (!draft) {
    return <EmptyPanel text="选择或新建一条规则后，可在这里输入测试文本。" />
  }

  return (
    <div className="space-y-5">
      <div>
        <Label htmlFor="rule-test-text">输入文本</Label>
        <Textarea
          className="mt-2 h-64 max-h-64 resize-none overflow-y-auto [field-sizing:fixed]"
          id="rule-test-text"
          onChange={(event) => onUpdateTestText(event.target.value)}
          placeholder="粘贴需要验证的原始文本"
          value={draft.testText}
        />
      </div>
      <Button className="w-full" disabled={test.isRunning} onClick={test.run}>
        <Play />
        {test.isRunning ? "正在运行" : "运行测试"}
      </Button>
      <section className="border-y border-border py-4">
        <div className="flex items-center gap-2 text-sm font-medium"><FlaskConical className="size-4 text-primary" />测试结果</div>
        {test.error ? <p className="mt-3 text-sm leading-6 text-destructive">{getApiErrorMessage(test.error, "运行测试失败。")}</p> : null}
        {test.result ? <pre className="mt-3 max-h-80 overflow-auto rounded-lg bg-muted p-3 text-xs leading-5 text-muted-foreground">{JSON.stringify(test.result, null, 2)}</pre> : null}
        {!test.error && !test.result ? <p className="mt-3 text-sm leading-6 text-muted-foreground">运行会将当前草稿直接提交到 Engine processor，不会保存到规则库。</p> : null}
      </section>
    </div>
  )
}

function EmptyPanel({ text }: { text: string }) {
  return <div className="grid min-h-64 place-items-center text-center text-sm leading-6 text-muted-foreground">{text}</div>
}
