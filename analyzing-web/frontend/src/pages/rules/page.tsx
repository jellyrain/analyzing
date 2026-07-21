import { Navigate } from "react-router"

import { getApiErrorMessage } from "@/api/http"
import { useHostBootstrap } from "@/features/connection/use-host-bootstrap"
import { AppShell } from "@/layout/app-shell"
import { LoadingPage } from "@/pages/common/loading-page"
import { ServiceErrorPage } from "@/pages/common/service-error-page"
import { RuleEditor } from "@/pages/rules/components/rule-editor"
import { RuleInspector } from "@/pages/rules/components/rule-inspector"
import { RuleList } from "@/pages/rules/components/rule-list"
import { RuleNodeDrawer } from "@/pages/rules/components/rule-node-drawer"
import { useCatalogPlugins } from "@/pages/rules/hooks/use-catalog-plugins"
import { useMappingPreview } from "@/pages/rules/hooks/use-mapping-preview"
import { useRuleDrafts } from "@/pages/rules/hooks/use-rule-drafts"

/** 规则配置初版：本地草稿编辑器，等待 Engine CRUD 接入后替换数据来源。 */
export function RulesPage() {
  const bootstrapQuery = useHostBootstrap()
  const drafts = useRuleDrafts()
  const mappingPreview = useMappingPreview(drafts.activeDraft)
  const catalogPluginsQuery = useCatalogPlugins(
    bootstrapQuery.data?.configured ?? false
  )
  const catalogPlugins = catalogPluginsQuery.data ?? []
  const splitters = catalogPlugins.filter(
    (plugin) => plugin.plugin_type === "splitter"
  )
  const parsers = catalogPlugins.filter(
    (plugin) => plugin.plugin_type === "parser"
  )

  if (bootstrapQuery.isPending) {
    return (
      <LoadingPage
        description="正在读取 Host 连接配置。"
        label="ANALYZING WEB"
        title="正在准备规则配置"
      />
    )
  }

  if (bootstrapQuery.isError) {
    return (
      <ServiceErrorPage
        description={getApiErrorMessage(
          bootstrapQuery.error,
          "请确认 Web Host 后端已经启动。"
        )}
        label="HOST UNAVAILABLE"
        onRetry={() => void bootstrapQuery.refetch()}
        title="无法打开规则配置"
      />
    )
  }

  if (!bootstrapQuery.data.configured) {
    return <Navigate replace to="/settings" />
  }

  return (
    <AppShell activePage="rules" contentScrollable={false}>
      <div className="grid h-full min-h-0 lg:grid-cols-[14rem_minmax(0,1fr)] xl:grid-cols-[14rem_minmax(0,1fr)_22rem]">
        <RuleList
          activeDraftId={drafts.activeDraftId}
          drafts={drafts.drafts}
          onCreate={drafts.createDraft}
          onDelete={drafts.deleteDraft}
          onSelect={drafts.selectDraft}
        />
        <RuleEditor
          activeTab={drafts.activeTab}
          draft={drafts.activeDraft}
          onAddMappings={drafts.addMappings}
          onAddPipelineNode={drafts.addPipelineNode}
          onAddSplitStep={drafts.addSplitStep}
          onDeleteMapping={drafts.deleteMapping}
          onDeletePipelineNode={drafts.deletePipelineNode}
          onDeleteSplitStep={drafts.deleteSplitStep}
          onClearSelection={drafts.clearSelectedEditorItem}
          onExportDraft={drafts.exportActiveDraft}
          onImportDraft={drafts.importLocalFile}
          onImportJson={drafts.importLocalJson}
          onSaveLocal={drafts.saveLocal}
          onSelectItem={drafts.selectEditorItem}
          onTabChange={(tab) => {
            drafts.setActiveTab(tab)
            if (tab === "mapping") mappingPreview.run()
          }}
          onUpdateDraftName={drafts.updateDraftName}
          onUpdateMapping={drafts.updateMapping}
          mappingPreview={mappingPreview}
          parsers={parsers}
          selectedItem={drafts.selectedEditorItem}
          splitters={splitters}
        />
        <div className="hidden min-h-0 xl:block">
          <RuleInspector
            draft={drafts.activeDraft}
            onUpdateTestText={drafts.updateTestText}
          />
        </div>
        <RuleNodeDrawer
          draft={drafts.activeDraft}
          onOpenChange={(open) => {
            if (!open) drafts.clearSelectedEditorItem()
          }}
          onUpdatePipelineNode={drafts.updatePipelineNode}
          onUpdateSplitStep={drafts.updateSplitStep}
          open={drafts.selectedEditorItem !== null}
          parsers={parsers}
          selectedItem={drafts.selectedEditorItem}
          splitters={splitters}
        />
      </div>
    </AppShell>
  )
}
