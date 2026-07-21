import { LoaderCircle, RefreshCw, Settings2 } from "lucide-react"

import type { CatalogPlugin } from "@/api/engine-plugins"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { PluginParameterForm } from "@/pages/rules/components/plugin-parameter-form"
import { getDefaultParams } from "@/pages/rules/plugin-form-utils"
import { useParentFieldOptions } from "@/pages/rules/hooks/use-parent-field-options"
import type { PipelineNode, RuleDraft, RuleEditorItem, SplitStep } from "@/pages/rules/types"

type RuleNodeDrawerProps = {
  draft: RuleDraft | null
  onOpenChange: (open: boolean) => void
  onUpdatePipelineNode: (nodeId: string, patch: Partial<PipelineNode>) => void
  onUpdateSplitStep: (stepId: string, patch: Partial<SplitStep>) => void
  open: boolean
  parsers: CatalogPlugin[]
  selectedItem: RuleEditorItem | null
  splitters: CatalogPlugin[]
}

/** 节点配置抽屉只在选中流程节点时出现，不占用规则测试区域。 */
export function RuleNodeDrawer({ draft, onOpenChange, onUpdatePipelineNode, onUpdateSplitStep, open, parsers, selectedItem, splitters }: RuleNodeDrawerProps) {
  return (
    <Sheet onOpenChange={onOpenChange} open={open}>
      <SheetContent className="gap-0 p-0 sm:max-w-[30rem]" side="right">
        <SheetHeader className="border-b border-border pr-12">
          <p className="text-xs font-semibold tracking-[0.14em] text-primary">
            NODE CONFIGURATION
          </p>
          <SheetTitle className="mt-1 flex items-center gap-2">
            <Settings2 className="size-4 text-primary" />
            节点配置
          </SheetTitle>
          <SheetDescription>
            修改会直接写入当前配置，关闭抽屉后可继续测试规则。
          </SheetDescription>
        </SheetHeader>
        <ScrollArea className="min-h-0 flex-1">
          <div className="px-5 py-5">
            <NodeConfiguration
              draft={draft}
              onUpdatePipelineNode={onUpdatePipelineNode}
              onUpdateSplitStep={onUpdateSplitStep}
              parsers={parsers}
              selectedItem={selectedItem}
              splitters={splitters}
            />
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}

function NodeConfiguration({ draft, onUpdatePipelineNode, onUpdateSplitStep, parsers, selectedItem, splitters }: Omit<RuleNodeDrawerProps, "onOpenChange" | "open">) {
  if (!draft || !selectedItem) return null
  if (selectedItem.kind === "split") {
    const step = draft.splitSteps.find((item) => item.id === selectedItem.id)
    return step ? <SplitConfiguration onUpdate={(patch) => onUpdateSplitStep(step.id, patch)} plugins={splitters} step={step} /> : null
  }
  const node = findPipelineNode(draft.pipelineNodes, selectedItem.id)
  return node ? <ParserConfiguration draft={draft} node={node} onUpdate={(patch) => onUpdatePipelineNode(node.id, patch)} plugins={parsers} /> : null
}

function SplitConfiguration({ onUpdate, plugins, step }: { onUpdate: (patch: Partial<SplitStep>) => void; plugins: CatalogPlugin[]; step: SplitStep }) {
  const plugin = plugins.find((item) => item.plugin_id === step.pluginId)
  return <div className="space-y-5"><SectionTitle description="选择切分器并设置它的运行参数。" title="切分步骤" /><PluginPicker label="切分器插件" onSelect={(next) => onUpdate({ pluginId: next.plugin_id, params: getDefaultParams(next.form_schema) })} plugins={plugins} value={step.pluginId} />{plugin ? <PluginParameters onChange={(params) => onUpdate({ params })} params={step.params} plugin={plugin} /> : <ChoosePluginHint />}</div>
}

function ParserConfiguration({ draft, node, onUpdate, plugins }: { draft: RuleDraft; node: PipelineNode; onUpdate: (patch: Partial<PipelineNode>) => void; plugins: CatalogPlugin[] }) {
  const plugin = plugins.find((item) => item.plugin_id === node.parserId)
  const isRoot = draft.pipelineNodes.some((root) => root.id === node.id)
  return <div className="space-y-5"><SectionTitle description="设置解析器、父级字段和输出层级。" title="解析节点" /><div className="grid gap-4 border-y border-border py-4">{isRoot ? <p className="text-sm leading-6 text-muted-foreground">这是根解析节点，不需要设置父级字段。</p> : <ParentFieldSelector draft={draft} node={node} onUpdate={onUpdate} />}<div className="grid gap-2"><Label htmlFor={`alias-prefix-${node.id}`}>拍平别名前缀</Label><Input id={`alias-prefix-${node.id}`} className="font-mono" onChange={(event) => onUpdate({ aliasPrefix: event.target.value })} placeholder="可选，例如 entity" value={node.aliasPrefix} /></div><div className="flex items-center justify-between gap-3"><div><Label>输出结构</Label><p className="mt-1 text-xs leading-5 text-muted-foreground">控制子层解析结果是否拍平到当前节点。</p></div><Button onClick={() => onUpdate({ flatten: !node.flatten })} size="sm" variant={node.flatten ? "secondary" : "outline"}>{node.flatten ? "已拍平" : "保留层级"}</Button></div></div><PluginPicker label="解析器插件" onSelect={(next) => onUpdate({ parserId: next.plugin_id, params: getDefaultParams(next.form_schema) })} plugins={plugins} value={node.parserId} />{plugin ? <PluginParameters onChange={(params) => onUpdate({ params })} params={node.params} plugin={plugin} /> : <ChoosePluginHint />}</div>
}

function ParentFieldSelector({ draft, node, onUpdate }: { draft: RuleDraft; node: PipelineNode; onUpdate: (patch: Partial<PipelineNode>) => void }) {
  const parentFields = useParentFieldOptions(draft, node.id)
  const fields = parentFields.hasSucceeded ? parentFields.fields : []
  const canSelect = fields.length > 0
  return <div className="grid gap-2"><div className="flex items-center justify-between gap-3"><Label htmlFor={`child-field-${node.id}`}>父级字段名</Label><Button disabled={parentFields.isLoading || !draft.testText.trim()} onClick={parentFields.load} size="sm" title={draft.testText.trim() ? "请求 Engine 解析父级链路" : "请先在规则测试中输入文本"} variant="outline">{parentFields.isLoading ? <LoaderCircle className="animate-spin" /> : <RefreshCw />}获取字段</Button></div><Input id={`child-field-${node.id}`} className="font-mono" onChange={(event) => onUpdate({ childField: event.target.value })} placeholder="可手工输入，或通过解析获取候选字段" value={node.childField} /><Select disabled={!canSelect} onValueChange={(field) => { if (field !== null) onUpdate({ childField: field }) }} value={canSelect && fields.includes(node.childField) ? node.childField : undefined}><SelectTrigger className="w-full"><SelectValue placeholder={canSelect ? "从解析结果选择父级字段" : "请先成功获取字段"} /></SelectTrigger><SelectContent align="start" className="min-w-64">{fields.map((field) => <SelectItem key={field} value={field}>{field}</SelectItem>)}</SelectContent></Select>{parentFields.hasSucceeded && !canSelect ? <p className="text-xs leading-5 text-muted-foreground">本次解析未识别到可作为子节点入口的字段。</p> : null}{!parentFields.hasSucceeded && !parentFields.error ? <p className="text-xs leading-5 text-muted-foreground">输入测试文本后点击“获取字段”，将请求 Engine 解析当前父级链路。</p> : null}{parentFields.error ? <p className="text-xs leading-5 text-destructive">{parentFields.error instanceof Error ? parentFields.error.message : "获取父级字段失败"}</p> : null}</div>
}

function SectionTitle({ description, title }: { description: string; title: string }) {
  return <div><h2 className="text-base font-semibold">{title}</h2><p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p></div>
}

function ChoosePluginHint() {
  return <p className="border-y border-border py-4 text-sm leading-6 text-muted-foreground">先选择一个插件，系统会根据插件的 form.schema.json 显示可配置字段。</p>
}

function PluginParameters({ onChange, params, plugin }: { onChange: (params: SplitStep["params"]) => void; params: SplitStep["params"]; plugin: CatalogPlugin }) {
  if (Object.keys(plugin.form_schema?.fields ?? {}).length === 0) return <section className="border-y border-border py-4"><h3 className="text-sm font-medium">插件参数</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">此插件没有可配置参数，选择后可直接参与规则执行。</p></section>
  return <PluginParameterForm onChange={onChange} params={params} schema={plugin.form_schema} />
}

function PluginPicker({ label, onSelect, plugins, value }: { label: string; onSelect: (plugin: CatalogPlugin) => void; plugins: CatalogPlugin[]; value: string }) {
  return <div className="grid gap-2"><Label>{label}</Label><Select onValueChange={(pluginId) => { const plugin = plugins.find((item) => item.plugin_id === pluginId); if (plugin) onSelect(plugin) }} value={value || undefined}><SelectTrigger className="w-full"><SelectValue placeholder={plugins.length === 0 ? "未发现可用插件" : "选择插件"} /></SelectTrigger><SelectContent align="start" className="min-w-80 max-w-[calc(100vw-2rem)]">{plugins.map((plugin) => <SelectItem key={plugin.plugin_id} value={plugin.plugin_id}>{plugin.name} · {plugin.plugin_id}</SelectItem>)}</SelectContent></Select></div>
}

function findPipelineNode(nodes: PipelineNode[], nodeId: string): PipelineNode | null {
  for (const node of nodes) {
    if (node.id === nodeId) return node
    const child = findPipelineNode(node.children, nodeId)
    if (child) return child
  }
  return null
}
