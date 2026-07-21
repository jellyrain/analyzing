import { useState } from "react"
import { ChevronDown, ChevronRight, Code2, GitBranch, Plus, RefreshCw, Split, Trash2, Waypoints } from "lucide-react"

import type { CatalogPlugin } from "@/api/engine-plugins"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { RuleActions } from "@/pages/rules/components/rule-actions"
import { MappingSelectorDialog } from "@/pages/rules/components/mapping-selector-dialog"
import type { MappingPreviewState } from "@/pages/rules/hooks/use-mapping-preview"
import { useRuleTreeCollapse } from "@/pages/rules/hooks/use-rule-tree-collapse"
import type {
  FieldMapping,
  PipelineNode,
  RuleDraft,
  RuleEditorItem,
  RuleTab,
  SplitStep,
} from "@/pages/rules/types"

type RuleEditorProps = {
  activeTab: RuleTab
  draft: RuleDraft | null
  onAddMappings: (mappings: Array<Pick<FieldMapping, "source" | "target">>) => void
  onAddPipelineNode: (parentId?: string) => void
  onAddSplitStep: () => void
  onDeleteMapping: (mappingId: string) => void
  onDeletePipelineNode: (nodeId: string) => void
  onDeleteSplitStep: (stepId: string) => void
  onClearSelection: () => void
  onExportDraft: () => void
  onImportDraft: (file: File) => Promise<void>
  onImportJson: (text: string) => Promise<void>
  onSaveLocal: () => void
  onSelectItem: (item: RuleEditorItem) => void
  onTabChange: (tab: RuleTab) => void
  onUpdateDraftName: (name: string) => void
  onUpdateMapping: (mappingId: string, patch: Partial<FieldMapping>) => void
  mappingPreview: MappingPreviewState
  parsers: CatalogPlugin[]
  selectedItem: RuleEditorItem | null
  splitters: CatalogPlugin[]
}

/** 中央区域只呈现规则结构；节点参数统一在右侧检查器编辑。 */
export function RuleEditor({
  activeTab,
  draft,
  onAddMappings,
  onAddPipelineNode,
  onAddSplitStep,
  onDeleteMapping,
  onDeletePipelineNode,
  onDeleteSplitStep,
  onClearSelection,
  onExportDraft,
  onImportDraft,
  onImportJson,
  onSaveLocal,
  onSelectItem,
  onTabChange,
  onUpdateDraftName,
  onUpdateMapping,
  mappingPreview,
  parsers,
  selectedItem,
  splitters,
}: RuleEditorProps) {
  const treeCollapse = useRuleTreeCollapse()
  const [isMappingSelectorOpen, setIsMappingSelectorOpen] = useState(false)

  if (!draft) {
    return (
      <section className="grid min-h-0 place-items-center px-6">
        <div className="max-w-sm text-center">
          <div className="mx-auto grid size-11 place-items-center rounded-lg bg-primary/10 text-primary">
            <Waypoints />
          </div>
          <h1 className="mt-5 text-xl font-semibold">从一条规则开始</h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            先在左侧新建规则。编辑器会以流程树组织切分、解析和字段映射。
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="flex min-h-0 flex-col">
      <header className="flex flex-wrap items-center gap-3 border-b border-border px-5 py-3 sm:px-7">
        <div className="min-w-0 flex-1">
          <Label className="sr-only" htmlFor="rule-name">
            规则名称
          </Label>
          <Input
            id="rule-name"
            onChange={(event) => onUpdateDraftName(event.target.value)}
            value={draft.name}
          />
        </div>
        <RuleActions
          draft={draft}
          onExportFile={onExportDraft}
          onImportFile={onImportDraft}
          onImportText={onImportJson}
          onSave={onSaveLocal}
        />
      </header>

      <Tabs
        className="flex min-h-0 flex-1 flex-col"
        onValueChange={(value) => onTabChange(value as RuleTab)}
        value={activeTab}
      >
        <div className="border-b border-border px-5 sm:px-7">
          <TabsList aria-label="规则编辑区" className="h-11 w-full justify-start gap-5 rounded-none p-0" variant="line">
            <TabsTrigger className="h-full flex-none rounded-none px-0" value="split">切分规则</TabsTrigger>
            <TabsTrigger className="h-full flex-none rounded-none px-0" value="pipeline">解析流水线</TabsTrigger>
            <TabsTrigger className="h-full flex-none rounded-none px-0" value="mapping">字段映射</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent className="min-h-0 flex-1 data-[state=inactive]:hidden" value="split">
          <ScrollArea className="h-full">
            <div className="min-h-full px-5 py-5 sm:px-7" onClick={onClearSelection}>
            <div className="mx-auto max-w-6xl">
              <EditorSection actionLabel="添加切分步骤" icon={<Split />} onAction={onAddSplitStep} title="切分规则">
                {draft.splitSteps.length === 0 ? (
                  <EmptyEditor text="还没有切分步骤。按顺序添加文本预处理或正则切分。" />
                ) : (
                  <div className="space-y-3">
                    {draft.splitSteps.map((step, index) => (
                      <SplitStepSummary
                        index={index}
                        isSelected={selectedItem?.kind === "split" && selectedItem.id === step.id}
                        key={step.id}
                        onDelete={() => onDeleteSplitStep(step.id)}
                        onSelect={() => onSelectItem({ id: step.id, kind: "split" })}
                        plugins={splitters}
                        step={step}
                      />
                    ))}
                  </div>
                )}
              </EditorSection>
            </div></div>
          </ScrollArea>
        </TabsContent>

        <TabsContent className="min-h-0 flex-1 data-[state=inactive]:hidden" value="pipeline">
          <ScrollArea className="h-full">
            <div className="min-h-full px-5 py-5 sm:px-7" onClick={onClearSelection}>
            <div className="mx-auto max-w-6xl">
              <EditorSection
                actionLabel="添加根节点"
                icon={<GitBranch />}
                onAction={() => onAddPipelineNode()}
                title="解析流水线"
              >
                {draft.pipelineNodes.length === 0 ? (
                  <EmptyEditor text="还没有解析节点。先添加根节点，再逐层补充子节点。" />
                ) : (
                  <div className="space-y-3">
                    {draft.pipelineNodes.map((node) => (
                      <PipelineNodeSummary
                        isSelected={selectedItem?.kind === "parser" && selectedItem.id === node.id}
                        isNodeCollapsed={treeCollapse.isCollapsed}
                        key={node.id}
                        level={0}
                        node={node}
                        onAddChild={onAddPipelineNode}
                        onDelete={onDeletePipelineNode}
                        onSelect={(nodeId) => onSelectItem({ id: nodeId, kind: "parser" })}
                        onToggleCollapse={treeCollapse.toggleNode}
                        plugins={parsers}
                        selectedItem={selectedItem}
                      />
                    ))}
                  </div>
                )}
              </EditorSection>
            </div></div>
          </ScrollArea>
        </TabsContent>

        <TabsContent className="min-h-0 flex-1 data-[state=inactive]:hidden" value="mapping">
          <ScrollArea className="h-full">
            <div className="min-h-full px-5 py-5 sm:px-7" onClick={onClearSelection}>
            <div className="mx-auto max-w-6xl">
              <EditorSection actionDisabled={!mappingPreview.isReady || mappingPreview.candidates.length === 0} actionLabel="添加字段映射" icon={<Waypoints />} onAction={() => setIsMappingSelectorOpen(true)} title="字段映射">
                {mappingPreview.isLoading ? (
                  <MappingPreviewMessage text="正在请求 Engine 解析当前规则，完成后即可选择 parsed 字段。" />
                ) : mappingPreview.error ? (
                  <MappingPreviewMessage
                    actionLabel="重新解析"
                    onAction={mappingPreview.run}
                    text={mappingPreview.error.message}
                  />
                ) : !mappingPreview.isReady ? (
                  <MappingPreviewMessage text="进入字段映射页后会自动解析当前规则。" />
                ) : mappingPreview.candidates.length === 0 ? (
                  <MappingPreviewMessage
                    actionLabel="重新解析"
                    onAction={mappingPreview.run}
                    text="本次解析没有产出可映射的叶子字段。"
                  />
                ) : draft.mappings.length === 0 ? (
                  <EmptyEditor text="还没有字段映射。解析测试接入后，可将结果字段映射为业务输出。" />
                ) : (
                  <div className="space-y-3">
                    {draft.mappings.map((mapping) => (
                      <MappingEditor
                        key={mapping.id}
                        mapping={mapping}
                        onDelete={() => onDeleteMapping(mapping.id)}
                        onUpdate={(patch) => onUpdateMapping(mapping.id, patch)}
                      />
                    ))}
                  </div>
                )}
              </EditorSection>
              {isMappingSelectorOpen ? <MappingSelectorDialog
                candidates={mappingPreview.candidates}
                onAdd={(candidates) => onAddMappings(candidates.map((candidate) => ({ source: candidate.path, target: candidate.alias })))}
                onOpenChange={setIsMappingSelectorOpen}
                open
              /> : null}
            </div></div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </section>
  )
}

function EditorSection({ actionDisabled = false, actionLabel, children, icon, onAction, title }: {
  actionDisabled?: boolean
  actionLabel: string
  children: React.ReactNode
  icon: React.ReactNode
  onAction: () => void
  title: string
}) {
  return (
    <section>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold tracking-[0.14em] text-primary">RULE EDITOR</p>
          <h2 className="mt-2 text-lg font-semibold">{title}</h2>
        </div>
        <Button disabled={actionDisabled} onClick={onAction} variant="outline">
          {icon}
          {actionLabel}
        </Button>
      </header>
      <div className="mt-5">{children}</div>
    </section>
  )
}

function EmptyEditor({ text }: { text: string }) {
  return <div className="border-y border-border py-10 text-center text-sm leading-6 text-muted-foreground">{text}</div>
}

function MappingPreviewMessage({ actionLabel, onAction, text }: { actionLabel?: string; onAction?: () => void; text: string }) {
  return <div className="border-y border-border py-10 text-center text-sm leading-6 text-muted-foreground"><p>{text}</p>{actionLabel && onAction ? <Button className="mt-4" onClick={onAction} size="sm" variant="outline"><RefreshCw />{actionLabel}</Button> : null}</div>
}

function SplitStepSummary({ index, isSelected, onDelete, onSelect, plugins, step }: {
  index: number
  isSelected: boolean
  onDelete: () => void
  onSelect: () => void
  plugins: CatalogPlugin[]
  step: SplitStep
}) {
  const plugin = plugins.find((item) => item.plugin_id === step.pluginId)
  return (
    <article className={`grid cursor-pointer items-center gap-3 rounded-lg border px-4 py-2.5 transition-colors hover:border-primary/55 hover:bg-muted/35 sm:grid-cols-[2rem_minmax(0,1fr)_auto] ${isSelected ? "border-primary bg-primary/5" : "border-border bg-muted/20"}`} onClick={(event) => { event.stopPropagation(); onSelect() }}>
      <span className="text-xs font-semibold text-primary">{String(index + 1).padStart(2, "0")}</span>
      <PluginSummary plugin={plugin} unselectedText="尚未选择切分器" />
      <div className="flex items-center gap-1">
        <Button aria-label={`删除切分步骤 ${index + 1}`} onClick={(event) => { event.stopPropagation(); onDelete() }} size="icon" title="删除步骤" variant="ghost">
          <Trash2 />
        </Button>
      </div>
    </article>
  )
}

function PipelineNodeSummary({ isNodeCollapsed, isSelected, level, node, onAddChild, onDelete, onSelect, onToggleCollapse, plugins, selectedItem }: {
  isNodeCollapsed: (nodeId: string) => boolean
  isSelected: boolean
  level: number
  node: PipelineNode
  onAddChild: (nodeId: string) => void
  onDelete: (nodeId: string) => void
  onSelect: (nodeId: string) => void
  onToggleCollapse: (nodeId: string) => void
  plugins: CatalogPlugin[]
  selectedItem: RuleEditorItem | null
}) {
  const plugin = plugins.find((item) => item.plugin_id === node.parserId)
  const isCollapsed = isNodeCollapsed(node.id)
  return (
    <div className={level > 0 ? "ml-5 border-l border-border pl-4" : ""}>
      <article className={`grid cursor-pointer items-center gap-3 rounded-lg border px-4 py-2.5 transition-colors hover:border-primary/55 hover:bg-muted/35 sm:grid-cols-[minmax(0,1fr)_auto] ${isSelected ? "border-primary bg-primary/5" : "border-border bg-muted/20"}`} onClick={(event) => { event.stopPropagation(); onSelect(node.id) }}>
        <div className="min-w-0">
          <p className="text-xs font-medium text-muted-foreground">{level === 0 ? "根解析节点" : `子节点 · ${node.childField || "未设置父级字段"}`}</p>
          <div className="mt-1"><PluginSummary plugin={plugin} unselectedText="尚未选择解析器" /></div>
          <p className="mt-1 text-xs text-muted-foreground">{node.children.length} 个子节点 · {node.flatten ? "子层结果拍平" : "保留结果层级"}</p>
        </div>
        <div className="flex items-center gap-1">
          <Button aria-label="添加子节点" onClick={(event) => { event.stopPropagation(); onAddChild(node.id) }} size="icon" title="添加子节点" variant="ghost"><Plus /></Button>
          {node.children.length > 0 ? <Button aria-expanded={!isCollapsed} aria-label={isCollapsed ? "展开子节点" : "收起子节点"} onClick={(event) => { event.stopPropagation(); onToggleCollapse(node.id) }} size="icon" title={isCollapsed ? "展开子节点" : "收起子节点"} variant="ghost">{isCollapsed ? <ChevronRight /> : <ChevronDown />}</Button> : null}
          <Button aria-label="删除节点" onClick={(event) => { event.stopPropagation(); onDelete(node.id) }} size="icon" title="删除节点" variant="ghost"><Trash2 /></Button>
        </div>
      </article>
      {node.children.length > 0 && !isCollapsed ? (
        <div className="mt-2 space-y-2">
          {node.children.map((child) => (
            <PipelineNodeSummary
              isSelected={selectedItem?.kind === "parser" && selectedItem.id === child.id}
              isNodeCollapsed={isNodeCollapsed}
              key={child.id}
              level={level + 1}
              node={child}
              onAddChild={onAddChild}
              onDelete={onDelete}
              onSelect={onSelect}
              onToggleCollapse={onToggleCollapse}
              plugins={plugins}
              selectedItem={selectedItem}
            />
          ))}
        </div>
      ) : null}
    </div>
  )
}

function PluginSummary({ plugin, unselectedText }: { plugin?: CatalogPlugin; unselectedText: string }) {
  if (!plugin) return <p className="text-sm text-muted-foreground">{unselectedText}</p>
  const parameterCount = Object.keys(plugin.form_schema?.fields ?? {}).length
  return (
    <div className="min-w-0">
      <p className="truncate text-sm font-medium">{plugin.name}</p>
      <p className="mt-1 truncate font-mono text-xs text-muted-foreground">{plugin.plugin_id} · {parameterCount === 0 ? "无需参数" : `${parameterCount} 个参数`}</p>
    </div>
  )
}

function MappingEditor({ mapping, onDelete, onUpdate }: {
  mapping: FieldMapping
  onDelete: () => void
  onUpdate: (patch: Partial<FieldMapping>) => void
}) {
  const [allowManualSource, setAllowManualSource] = useState(false)
  return (
    <div className="grid items-center gap-2 rounded-lg border border-border bg-muted/20 px-3 py-2 sm:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)_auto_auto]">
      <Input aria-label="目标字段" className="font-mono" onChange={(event) => onUpdate({ target: event.target.value })} placeholder="目标字段，例如 diagnosis" value={mapping.target} />
      {allowManualSource ? <Input aria-label="JSONPath" className="font-mono" onChange={(event) => onUpdate({ source: event.target.value })} placeholder='$["字段"][0]' value={mapping.source} /> : <p className="truncate font-mono text-xs text-muted-foreground" title={mapping.source}>{mapping.source}</p>}
      <Button aria-label={allowManualSource ? "关闭手动 JSONPath" : "允许手动改 JSONPath"} onClick={() => setAllowManualSource((current) => !current)} size="icon" title={allowManualSource ? "关闭手动 JSONPath" : "允许手动改 JSONPath"} variant={allowManualSource ? "secondary" : "ghost"}><Code2 /></Button>
      <Button aria-label="删除字段映射" onClick={onDelete} size="icon" title="删除字段映射" variant="ghost"><Trash2 /></Button>
    </div>
  )
}
