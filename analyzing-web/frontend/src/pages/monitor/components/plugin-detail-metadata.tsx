import type { PluginDetail } from "@/api/engine-monitor"

type RecordValue = Record<string, unknown>

function isRecord(value: unknown): value is RecordValue {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function getText(value: unknown) {
  if (typeof value === "string" || typeof value === "number") {
    return String(value)
  }

  if (typeof value === "boolean") {
    return value ? "是" : "否"
  }

  return "--"
}

function getFieldLabel(fieldId: string, field: RecordValue) {
  return typeof field.label === "string" && field.label ? field.label : fieldId
}

/** 将插件接口返回的能力与表单 schema 呈现为可读的配置说明，不暴露原始 JSON。 */
export function PluginDetailMetadata({ detail }: { detail: PluginDetail }) {
  const capabilities = Object.entries(detail.capabilities)
  const formSchema = detail.form_schema
  const fields = isRecord(formSchema.fields) ? formSchema.fields : {}
  const sections = Array.isArray(formSchema.sections)
    ? formSchema.sections.filter(isRecord)
    : []
  const sectionFieldIds = new Set(
    sections.flatMap((section) =>
      Array.isArray(section.fields)
        ? section.fields.filter(
            (fieldId): fieldId is string => typeof fieldId === "string"
          )
        : []
    )
  )
  const ungroupedFieldIds = Object.keys(fields).filter(
    (fieldId) => !sectionFieldIds.has(fieldId)
  )

  return (
    <div className="mt-7 space-y-7">
      <section className="border-t border-border pt-4">
        <h3 className="text-sm font-semibold">插件说明</h3>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {detail.description || detail.summary || "该插件暂未提供说明。"}
        </p>
      </section>

      {capabilities.length > 0 ? (
        <section className="border-t border-border pt-4">
          <h3 className="text-sm font-semibold">执行能力</h3>
          <dl className="mt-3 divide-y divide-border text-sm">
            {capabilities.map(([key, value]) => (
              <div
                className="flex items-center justify-between gap-4 py-2.5"
                key={key}
              >
                <dt className="font-mono text-xs text-muted-foreground">
                  {key}
                </dt>
                <dd className="text-right">{getText(value)}</dd>
              </div>
            ))}
          </dl>
        </section>
      ) : null}

      {Object.keys(fields).length > 0 ? (
        <section className="border-t border-border pt-4">
          <h3 className="text-sm font-semibold">参数定义</h3>
          <div className="mt-4 space-y-5">
            {sections.map((section, index) => {
              const fieldIds = Array.isArray(section.fields)
                ? section.fields.filter(
                    (fieldId): fieldId is string => typeof fieldId === "string"
                  )
                : []
              const title =
                typeof section.title === "string"
                  ? section.title
                  : `配置分组 ${index + 1}`

              return (
                <div key={`${title}-${index}`}>
                  <p className="text-xs font-medium text-primary">{title}</p>
                  <FieldList fieldIds={fieldIds} fields={fields} />
                </div>
              )
            })}
            {ungroupedFieldIds.length > 0 ? (
              <FieldList fieldIds={ungroupedFieldIds} fields={fields} />
            ) : null}
          </div>
        </section>
      ) : null}
    </div>
  )
}

function FieldList({
  fieldIds,
  fields,
}: {
  fieldIds: string[]
  fields: RecordValue
}) {
  return (
    <dl className="mt-2 divide-y divide-border text-sm">
      {fieldIds.map((fieldId) => {
        const field = isRecord(fields[fieldId]) ? fields[fieldId] : {}
        const metadata = [getText(field.type), getText(field.widget)]
          .filter((value) => value !== "--")
          .join(" / ")

        return (
          <div
            className="grid grid-cols-[minmax(0,1fr)_auto] gap-3 py-3"
            key={fieldId}
          >
            <div className="min-w-0">
              <dt className="font-medium">{getFieldLabel(fieldId, field)}</dt>
              <dd className="mt-1 font-mono text-xs text-muted-foreground">
                {fieldId}
                {metadata ? ` · ${metadata}` : ""}
              </dd>
            </div>
            <dd className="text-right text-xs text-muted-foreground">
              {field.required === true ? "必填" : "可选"}
            </dd>
          </div>
        )
      })}
    </dl>
  )
}
