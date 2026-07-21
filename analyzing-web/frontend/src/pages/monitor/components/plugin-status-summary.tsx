import type {
  InstallStatus,
  PluginStatusRecord,
  RuntimeStatus,
} from "@/api/engine-monitor"

type PluginStatusSummaryProps = {
  items: PluginStatusRecord[]
}

type StatusSegment<TStatus extends string> = {
  color: string
  label: string
  status: TStatus
}

const installSegments: StatusSegment<InstallStatus>[] = [
  { status: "installed", label: "已安装", color: "var(--chart-1)" },
  { status: "discovered", label: "已发现", color: "var(--chart-3)" },
  { status: "failed", label: "安装失败", color: "var(--destructive)" },
  { status: "removed", label: "已移除", color: "var(--muted-foreground)" },
]

const runtimeSegments: StatusSegment<RuntimeStatus>[] = [
  { status: "ready", label: "就绪", color: "var(--chart-1)" },
  { status: "loaded", label: "已加载", color: "var(--chart-2)" },
  { status: "registered", label: "已注册", color: "var(--chart-3)" },
  { status: "unavailable", label: "不可用", color: "var(--muted-foreground)" },
  { status: "error", label: "异常", color: "var(--destructive)" },
]

/** 基于插件状态接口展示当前安装和运行分布，不混入执行实例指标。 */
export function PluginStatusSummary({ items }: PluginStatusSummaryProps) {
  return (
    <section className="border-y border-border py-5">
      <header className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <p className="text-xs font-semibold tracking-[0.14em] text-primary">
            PLUGIN OVERVIEW
          </p>
          <h3 className="mt-2 text-base font-semibold">插件态势</h3>
        </div>
        <span className="text-sm text-muted-foreground">
          <strong className="font-semibold text-foreground">
            {items.length}
          </strong>{" "}
          个插件
        </span>
      </header>
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <StatusDistribution
          items={items}
          label="安装状态"
          segments={installSegments}
          valueKey="install_status"
        />
        <StatusDistribution
          items={items}
          label="运行状态"
          segments={runtimeSegments}
          valueKey="runtime_status"
        />
      </div>
    </section>
  )
}

function StatusDistribution<TStatus extends string>({
  items,
  label,
  segments,
  valueKey,
}: {
  items: PluginStatusRecord[]
  label: string
  segments: StatusSegment<TStatus>[]
  valueKey: "install_status" | "runtime_status"
}) {
  const countByStatus = new Map<TStatus, number>()

  for (const segment of segments) {
    countByStatus.set(segment.status, 0)
  }

  for (const item of items) {
    const status = item[valueKey] as TStatus
    countByStatus.set(status, (countByStatus.get(status) ?? 0) + 1)
  }

  const total = Math.max(items.length, 1)

  return (
    <section>
      <p className="text-sm font-medium">{label}</p>
      <div
        aria-label={label}
        className="mt-3 flex h-2.5 overflow-hidden rounded-full bg-muted"
      >
        {segments.map((segment) => {
          const count = countByStatus.get(segment.status) ?? 0

          return count > 0 ? (
            <span
              className="h-full"
              key={segment.status}
              style={{
                backgroundColor: segment.color,
                width: `${(count / total) * 100}%`,
              }}
              title={`${segment.label}: ${count}`}
            />
          ) : null
        })}
      </div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs">
        {segments.map((segment) => {
          const count = countByStatus.get(segment.status) ?? 0

          return (
            <span
              className="flex items-center gap-1.5 text-muted-foreground"
              key={segment.status}
            >
              <span
                className="size-1.5 rounded-full"
                style={{ backgroundColor: segment.color }}
              />
              {segment.label}
              <strong className="font-medium text-foreground">{count}</strong>
            </span>
          )
        })}
      </div>
    </section>
  )
}
