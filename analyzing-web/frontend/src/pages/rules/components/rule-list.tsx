import { FilePlus2, Trash2 } from "lucide-react"

import type { RuleDraft } from "@/pages/rules/types"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

type RuleListProps = {
  activeDraftId: string | null
  drafts: RuleDraft[]
  onCreate: () => void
  onDelete: (draftId: string) => void
  onSelect: (draftId: string) => void
}

/** 规则列表只呈现本地已创建草稿，后续可直接替换为 Engine 规则列表。 */
export function RuleList({
  activeDraftId,
  drafts,
  onCreate,
  onDelete,
  onSelect,
}: RuleListProps) {
  return (
    <aside className="flex min-h-0 flex-col border-r border-border bg-sidebar/35">
      <header className="flex items-center justify-between gap-3 border-b border-border px-4 py-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.14em] text-primary">
            RULES
          </p>
          <h2 className="mt-1 text-sm font-semibold">规则配置</h2>
        </div>
        <Button
          aria-label="新建规则"
          onClick={onCreate}
          size="icon-sm"
          title="新建规则"
          variant="outline"
        >
          <FilePlus2 />
        </Button>
      </header>

      <ScrollArea className="min-h-0 flex-1">
        {drafts.length === 0 ? (
          <div className="px-5 py-10 text-sm leading-6 text-muted-foreground">
            <p className="font-medium text-foreground">还没有规则草稿</p>
            <p className="mt-2">
              新建一个规则，从切分、解析和字段映射开始配置。
            </p>
            <Button
              className="mt-5 w-full"
              onClick={onCreate}
              variant="outline"
            >
              <FilePlus2 />
              新建规则
            </Button>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {drafts.map((draft) => {
              const active = draft.id === activeDraftId

              return (
                <div
                  className={
                    active
                      ? "group flex items-center gap-1 rounded-lg bg-sidebar-accent p-1"
                      : "group flex items-center gap-1 rounded-lg p-1 hover:bg-sidebar-accent/60"
                  }
                  key={draft.id}
                >
                  <button
                    aria-current={active ? "page" : undefined}
                    className={
                      active
                        ? "min-w-0 flex-1 truncate rounded-md px-2 py-2 text-left text-sm font-medium text-sidebar-accent-foreground"
                        : "min-w-0 flex-1 truncate rounded-md px-2 py-2 text-left text-sm text-muted-foreground"
                    }
                    onClick={() => onSelect(draft.id)}
                    type="button"
                  >
                    {draft.name || "未命名规则"}
                  </button>
                  <Button
                    aria-label={`删除规则 ${draft.name || "未命名规则"}`}
                    className="opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
                    onClick={() => onDelete(draft.id)}
                    size="icon-xs"
                    title="删除本地草稿"
                    variant="ghost"
                  >
                    <Trash2 />
                  </Button>
                </div>
              )
            })}
          </div>
        )}
      </ScrollArea>

      <footer className="border-t border-border px-4 py-3 text-xs leading-5 text-muted-foreground">
        保存后规则会保留在当前浏览器。Engine 规则 CRUD 接入后会在此加载和同步。
      </footer>
    </aside>
  )
}
