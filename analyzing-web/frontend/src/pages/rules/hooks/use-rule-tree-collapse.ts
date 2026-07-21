import { useState } from "react"

/** 管理规则树的折叠状态；未记录的节点默认保持展开。 */
export function useRuleTreeCollapse() {
  const [collapsedNodeIds, setCollapsedNodeIds] = useState<Set<string>>(
    () => new Set()
  )

  const toggleNode = (nodeId: string) => {
    setCollapsedNodeIds((current) => {
      const next = new Set(current)
      if (next.has(nodeId)) next.delete(nodeId)
      else next.add(nodeId)
      return next
    })
  }

  return {
    isCollapsed: (nodeId: string) => collapsedNodeIds.has(nodeId),
    toggleNode,
  }
}
