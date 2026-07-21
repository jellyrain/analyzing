import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { getApiErrorMessage } from "@/api/http"
import {
  getHostConfig,
  saveHostConfig,
  testHostConfig,
  type BootstrapResponse,
  type HostConfig,
} from "@/api/host"
import type { Feedback } from "@/pages/settings/types"

const DEFAULT_CONFIG: HostConfig = {
  engine_origin: "http://127.0.0.1:8000",
  monitor_refresh_seconds: 30,
}

/** 管理 Host 配置的查询、草稿、连通性测试与保存状态。 */
export function useHostConfig(configured: boolean) {
  const queryClient = useQueryClient()
  // 未编辑时直接使用 Query 数据，避免维护两份同步状态。
  const [draft, setDraft] = useState<HostConfig | null>(null)
  const [isDirty, setIsDirty] = useState(false)
  const [feedback, setFeedback] = useState<Feedback | null>(null)

  const configQuery = useQuery({
    queryKey: ["host", "config"],
    queryFn: getHostConfig,
    enabled: configured,
  })

  const testMutation = useMutation({ mutationFn: testHostConfig })
  const saveMutation = useMutation({ mutationFn: saveHostConfig })
  const form = draft ?? configQuery.data ?? DEFAULT_CONFIG

  const updateForm = (next: Partial<HostConfig>) => {
    setDraft((current) => ({ ...(current ?? form), ...next }))
    setIsDirty(true)
    setFeedback(null)
  }

  const runConnectionTest = async () => {
    setFeedback({ tone: "neutral", message: "正在连接 Engine，请稍候。" })

    try {
      const result = await testMutation.mutateAsync(form)
      setFeedback({
        tone: result.ok ? "success" : "error",
        message: result.status_code
          ? `${result.message}（HTTP ${result.status_code}）`
          : result.message,
      })
    } catch (error) {
      setFeedback({
        tone: "error",
        message: getApiErrorMessage(error, "连接测试失败，请检查 Engine 地址。"),
      })
    }
  }

  const saveConfig = async () => {
    setFeedback({ tone: "neutral", message: "正在保存本地配置。" })

    try {
      const savedConfig = await saveMutation.mutateAsync(form)
      queryClient.setQueryData<HostConfig>(["host", "config"], savedConfig)
      queryClient.setQueryData<BootstrapResponse>(["host", "bootstrap"], {
        configured: true,
        engine_origin: savedConfig.engine_origin,
      })
      setDraft(savedConfig)
      setIsDirty(false)
      setFeedback({
        tone: "success",
        message: "配置已保存。后续页面将通过本地 Host 连接此 Engine。",
      })
    } catch (error) {
      setFeedback({
        tone: "error",
        message: getApiErrorMessage(error, "保存失败，请检查填写内容。"),
      })
    }
  }

  const restoreSavedConfig = () => {
    if (!configQuery.data) {
      setDraft(DEFAULT_CONFIG)
      setIsDirty(false)
      return
    }

    setDraft(null)
    setIsDirty(false)
    setFeedback({ tone: "neutral", message: "已恢复最近一次保存的配置。" })
  }

  return {
    feedback,
    form,
    isBusy: testMutation.isPending || saveMutation.isPending,
    isDirty,
    isSaving: saveMutation.isPending,
    isTesting: testMutation.isPending,
    restoreSavedConfig,
    runConnectionTest,
    saveConfig,
    updateForm,
  }
}
