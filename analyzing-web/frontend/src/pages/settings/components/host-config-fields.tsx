import type { HostConfig } from "@/api/host"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

type HostConfigFieldsProps = {
  form: HostConfig
  idPrefix: string
  onUpdate: (next: Partial<HostConfig>) => void
}

/** 基础配置字段在首次连接页和工作区设置页中复用。 */
export function EngineOriginField({ form, idPrefix, onUpdate }: HostConfigFieldsProps) {
  const id = `${idPrefix}-engine-origin`

  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>Engine 根地址</Label>
      <Input
        className="h-11 bg-background/75 px-3"
        id={id}
        inputMode="url"
        onChange={(event) => onUpdate({ engine_origin: event.target.value })}
        placeholder="http://127.0.0.1:8000"
        required
        type="url"
        value={form.engine_origin}
      />
    </div>
  )
}

export function MonitorRefreshField({ form, idPrefix, onUpdate }: HostConfigFieldsProps) {
  const id = `${idPrefix}-monitor-refresh-seconds`

  return (
    <div className="grid max-w-xs gap-2">
      <Label htmlFor={id}>自动刷新间隔（秒）</Label>
      <Input
        className="h-11 bg-background/75 px-3"
        id={id}
        max={3600}
        min={1}
        onChange={(event) =>
          onUpdate({ monitor_refresh_seconds: Number(event.target.value) })
        }
        required
        type="number"
        value={form.monitor_refresh_seconds}
      />
    </div>
  )
}
