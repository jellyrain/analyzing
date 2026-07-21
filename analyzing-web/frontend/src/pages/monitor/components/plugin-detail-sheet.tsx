import type { PluginDetail, PluginStatusRecord } from "@/api/engine-monitor"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { PluginDetailMetadata } from "@/pages/monitor/components/plugin-detail-metadata"
import { MonitorStatusBadge } from "@/pages/monitor/components/monitor-status-badge"

type PluginDetailSheetProps = {
  detail: PluginDetail | undefined
  error: string | null
  isLoading: boolean
  plugin: PluginStatusRecord | null
  onOpenChange: (open: boolean) => void
}

function DetailRow({
  label,
  value,
}: {
  label: string
  value: string | number | boolean | null | undefined
}) {
  return (
    <div className="grid grid-cols-[7rem_minmax(0,1fr)] gap-3 border-b border-border py-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="break-all">
        {value === null || value === undefined ? "--" : String(value)}
      </span>
    </div>
  )
}

/** 点击插件状态后按插件 ID 请求 Engine 的完整插件登记信息。 */
export function PluginDetailSheet({
  detail,
  error,
  isLoading,
  plugin,
  onOpenChange,
}: PluginDetailSheetProps) {
  const runtimeStatus = detail?.runtime_status ?? plugin?.runtime_status

  return (
    <Sheet onOpenChange={onOpenChange} open={plugin !== null}>
      <SheetContent className="w-full gap-0 p-0 sm:max-w-xl">
        {plugin ? (
          <>
            <SheetHeader className="border-b border-border">
              <div className="flex items-center justify-between gap-4">
                <SheetTitle>插件运行详情</SheetTitle>
                {runtimeStatus ? (
                  <MonitorStatusBadge status={runtimeStatus} />
                ) : null}
              </div>
              <SheetDescription>
                {detail?.name ?? plugin.plugin_id} /{" "}
                {detail?.version ?? plugin.version ?? "未知版本"}
              </SheetDescription>
            </SheetHeader>
            <div className="overflow-auto p-4">
              {isLoading ? (
                <p className="py-8 text-sm text-muted-foreground">
                  正在读取插件完整详情...
                </p>
              ) : null}
              {error ? (
                <p className="py-8 text-sm text-destructive">{error}</p>
              ) : null}
              {detail ? (
                <>
                  <DetailRow label="插件 ID" value={detail.plugin_id} />
                  <DetailRow label="名称" value={detail.name} />
                  <DetailRow label="版本" value={detail.version} />
                  <DetailRow label="插件角色" value={detail.plugin_role} />
                  <DetailRow label="插件类型" value={detail.plugin_type} />
                  <DetailRow label="运行模式" value={detail.runtime_mode} />
                  <DetailRow label="加载策略" value={detail.load_strategy} />
                  <DetailRow
                    label="已启用"
                    value={detail.enabled ? "是" : "否"}
                  />
                  <DetailRow
                    label="兼容性"
                    value={detail.is_compatible ? "兼容" : "不兼容"}
                  />
                  <DetailRow label="安装状态" value={detail.install_status} />
                  <DetailRow label="运行状态" value={detail.runtime_status} />
                  <DetailRow label="安装目录" value={detail.plugin_dir} />
                  <DetailRow label="错误信息" value={detail.error_message} />
                  <PluginDetailMetadata detail={detail} />
                </>
              ) : null}
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  )
}
