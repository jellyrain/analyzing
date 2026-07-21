import { useState } from "react"

import type {
  FieldMapping,
  PipelineNode,
  RuleDraft,
  RuleEditorItem,
  RuleTab,
  SplitStep,
} from "@/pages/rules/types"
import {
  downloadRuleDraft,
  loadLocalRuleDrafts,
  readRuleDraftFile,
  readRuleDraftText,
  saveLocalRuleDrafts,
} from "@/pages/rules/rule-draft-storage"

function createId() {
  return crypto.randomUUID()
}

function updateDraft(
  drafts: RuleDraft[],
  draftId: string,
  updater: (draft: RuleDraft) => RuleDraft
) {
  return drafts.map((draft) => (draft.id === draftId ? updater(draft) : draft))
}

/** 管理规则配置初版的内存草稿；不写入 Host，也不伪造远端规则数据。 */
export function useRuleDrafts() {
  const [drafts, setDrafts] = useState<RuleDraft[]>(loadLocalRuleDrafts)
  const [activeDraftId, setActiveDraftId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<RuleTab>("split")
  const [inspectorTab, setInspectorTab] = useState<"config" | "test">("test")
  const [selectedEditorItem, setSelectedEditorItem] =
    useState<RuleEditorItem | null>(null)
  const activeDraft = drafts.find((draft) => draft.id === activeDraftId) ?? null

  const createDraft = () => {
    const draft: RuleDraft = {
      id: createId(),
      name: `未命名规则 ${drafts.length + 1}`,
      splitSteps: [],
      pipelineNodes: [],
      mappings: [],
      testText: "",
    }

    setDrafts((current) => [...current, draft])
    setActiveDraftId(draft.id)
    setActiveTab("split")
    setInspectorTab("test")
    setSelectedEditorItem(null)
    setInspectorTab("test")
  }

  const deleteDraft = (draftId: string) => {
    setDrafts((current) => current.filter((draft) => draft.id !== draftId))
    setActiveDraftId((current) => (current === draftId ? null : current))
    setSelectedEditorItem(null)
  }

  const saveLocal = () => {
    saveLocalRuleDrafts(drafts)
  }

  const exportActiveDraft = () => {
    if (activeDraft) downloadRuleDraft(activeDraft)
  }

  const replaceActiveDraft = (imported: RuleDraft) => {
    const draft = { ...imported, id: activeDraftId ?? createId() }
    setDrafts((current) => {
      const currentIndex = current.findIndex((item) => item.id === draft.id)
      return currentIndex === -1
        ? [...current, draft]
        : current.map((item) => (item.id === draft.id ? draft : item))
    })
    setActiveDraftId(draft.id)
    setActiveTab("split")
    setSelectedEditorItem(null)
    setInspectorTab("test")
  }

  const importLocalFile = async (file: File) => {
    replaceActiveDraft(await readRuleDraftFile(file))
  }

  const importLocalJson = async (text: string) => {
    replaceActiveDraft(readRuleDraftText(text))
  }

  const updateActiveDraft = (updater: (draft: RuleDraft) => RuleDraft) => {
    if (!activeDraftId) {
      return
    }

    setDrafts((current) => updateDraft(current, activeDraftId, updater))
  }

  const updateDraftName = (name: string) => {
    updateActiveDraft((draft) => ({ ...draft, name }))
  }

  const selectDraft = (draftId: string) => {
    setActiveDraftId(draftId)
    setSelectedEditorItem(null)
    setInspectorTab("test")
  }

  const selectEditorItem = (item: RuleEditorItem) => {
    setSelectedEditorItem(item)
    setInspectorTab("config")
  }

  const clearSelectedEditorItem = () => {
    setSelectedEditorItem(null)
    setInspectorTab("test")
  }

  const updateTestText = (testText: string) => {
    updateActiveDraft((draft) => ({ ...draft, testText }))
  }

  const addSplitStep = () => {
    const step: SplitStep = {
      id: createId(),
      params: {},
      pluginId: "",
    }
    updateActiveDraft((draft) => ({
      ...draft,
      splitSteps: [...draft.splitSteps, step],
    }))
    setSelectedEditorItem({ id: step.id, kind: "split" })
    setInspectorTab("config")
  }

  const updateSplitStep = (stepId: string, patch: Partial<SplitStep>) => {
    updateActiveDraft((draft) => ({
      ...draft,
      splitSteps: draft.splitSteps.map((step) =>
        step.id === stepId ? { ...step, ...patch } : step
      ),
    }))
  }

  const deleteSplitStep = (stepId: string) => {
    updateActiveDraft((draft) => ({
      ...draft,
      splitSteps: draft.splitSteps.filter((step) => step.id !== stepId),
    }))
    setSelectedEditorItem((current) =>
      current?.kind === "split" && current.id === stepId ? null : current
    )
    setInspectorTab("test")
  }

  const addPipelineNode = (parentId?: string) => {
    const node: PipelineNode = {
      aliasPrefix: "",
      childField: "",
      flatten: false,
      id: createId(),
      params: {},
      parserId: "",
      children: [],
    }

    const appendChild = (nodes: PipelineNode[]): PipelineNode[] =>
      nodes.map((item) =>
        item.id === parentId
          ? { ...item, children: [...item.children, node] }
          : { ...item, children: appendChild(item.children) }
      )

    updateActiveDraft((draft) => ({
      ...draft,
      pipelineNodes: parentId
        ? appendChild(draft.pipelineNodes)
        : [...draft.pipelineNodes, node],
    }))
    setSelectedEditorItem({ id: node.id, kind: "parser" })
    setInspectorTab("config")
  }

  const updatePipelineNode = (nodeId: string, patch: Partial<PipelineNode>) => {
    const updateNodes = (nodes: PipelineNode[]): PipelineNode[] =>
      nodes.map((node) =>
        node.id === nodeId
          ? { ...node, ...patch }
          : { ...node, children: updateNodes(node.children) }
      )

    updateActiveDraft((draft) => ({
      ...draft,
      pipelineNodes: updateNodes(draft.pipelineNodes),
    }))
  }

  const deletePipelineNode = (nodeId: string) => {
    const removeNode = (nodes: PipelineNode[]): PipelineNode[] =>
      nodes
        .filter((node) => node.id !== nodeId)
        .map((node) => ({ ...node, children: removeNode(node.children) }))

    updateActiveDraft((draft) => ({
      ...draft,
      pipelineNodes: removeNode(draft.pipelineNodes),
    }))
    setSelectedEditorItem((current) =>
      current?.kind === "parser" && current.id === nodeId ? null : current
    )
    setInspectorTab("test")
  }

  const addMapping = () => {
    const mapping: FieldMapping = { id: createId(), source: "", target: "" }
    updateActiveDraft((draft) => ({
      ...draft,
      mappings: [...draft.mappings, mapping],
    }))
  }

  const addMappings = (
    mappings: Array<Pick<FieldMapping, "source" | "target">>
  ) => {
    updateActiveDraft((draft) => {
      const existingSources = new Set(
        draft.mappings.map((mapping) => mapping.source)
      )
      const newMappings = mappings.filter((mapping) => {
        if (existingSources.has(mapping.source)) return false
        existingSources.add(mapping.source)
        return true
      })
      return {
        ...draft,
        mappings: [
          ...draft.mappings,
          ...newMappings.map((mapping) => ({ ...mapping, id: createId() })),
        ],
      }
    })
  }

  const updateMapping = (mappingId: string, patch: Partial<FieldMapping>) => {
    updateActiveDraft((draft) => ({
      ...draft,
      mappings: draft.mappings.map((mapping) =>
        mapping.id === mappingId ? { ...mapping, ...patch } : mapping
      ),
    }))
  }

  const deleteMapping = (mappingId: string) => {
    updateActiveDraft((draft) => ({
      ...draft,
      mappings: draft.mappings.filter((mapping) => mapping.id !== mappingId),
    }))
  }

  return {
    activeDraft,
    activeDraftId,
    activeTab,
    clearSelectedEditorItem,
    inspectorTab,
    selectedEditorItem,
    addMapping,
    addMappings,
    addPipelineNode,
    addSplitStep,
    createDraft,
    deleteDraft,
    deleteMapping,
    deletePipelineNode,
    deleteSplitStep,
    drafts,
    exportActiveDraft,
    importLocalFile,
    importLocalJson,
    setActiveDraftId,
    selectEditorItem,
    selectDraft,
    saveLocal,
    setActiveTab,
    updateDraftName,
    updateMapping,
    updatePipelineNode,
    updateSplitStep,
    updateTestText,
  }
}
