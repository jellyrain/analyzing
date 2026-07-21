import { getApiErrorMessage } from "@/api/http"
import { useHostBootstrap } from "@/features/connection/use-host-bootstrap"
import { LoadingPage } from "@/pages/common/loading-page"
import { ServiceErrorPage } from "@/pages/common/service-error-page"
import { SetupSettingsView } from "@/pages/settings/components/setup-settings-view"
import { WorkspaceSettingsView } from "@/pages/settings/components/workspace-settings-view"
import { useHostConfig } from "@/pages/settings/hooks/use-host-config"

/** 设置路由页，仅选择首次连接或已配置工作区视图。 */
export function SettingsPage() {
  const bootstrapQuery = useHostBootstrap()
  // 配置 hook 始终调用，bootstrap 未完成时仅禁用其远程查询。
  const state = useHostConfig(bootstrapQuery.data?.configured ?? false)

  if (bootstrapQuery.isPending) {
    return (
      <LoadingPage
        description="正在确认当前 Web Host 是否已经连接到 Engine。"
        label="ANALYZING WEB"
        title="正在读取本地配置"
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
        title="无法读取本地配置"
      />
    )
  }

  const configured = bootstrapQuery.data.configured
  const actions = {
    onRestore: state.restoreSavedConfig,
    onSave: () => void state.saveConfig(),
    onTest: () => void state.runConnectionTest(),
    onUpdate: state.updateForm,
  }

  if (configured) {
    return <WorkspaceSettingsView {...state} {...actions} />
  }

  return <SetupSettingsView {...state} {...actions} />
}
