import { Minus, Plus } from "lucide-react"

import type { PluginFormField, PluginFormSchema } from "@/api/engine-plugins"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import type { JsonValue } from "@/pages/rules/types"

type PluginParameterFormProps = {
  onChange: (params: Record<string, JsonValue>) => void
  params: Record<string, JsonValue>
  schema: PluginFormSchema
}

/** 将插件 form.schema.json 渲染为可直接提交给插件的参数控件。 */
export function PluginParameterForm({
  onChange,
  params,
  schema,
}: PluginParameterFormProps) {
  const fields = schema?.fields ?? {}
  const schemaSections = schema?.sections ?? []
  const sections =
    schemaSections.length > 0
      ? schemaSections
      : [{ title: "插件参数", fields: Object.keys(fields) }]

  return (
    <div className="col-span-full space-y-5 border-t border-border pt-4">
      {sections.map((section) => (
        <section key={section.title}>
          <p className="text-xs font-medium text-primary">{section.title}</p>
          <div className="mt-3 grid gap-4">
            {section.fields.map((fieldId) => {
              const field = fields[fieldId]
              return field ? (
                <ParameterField
                  field={field}
                  fieldId={fieldId}
                  key={fieldId}
                  onChange={(value) =>
                    onChange({ ...params, [fieldId]: value })
                  }
                  value={params[fieldId]}
                />
              ) : null
            })}
          </div>
        </section>
      ))}
    </div>
  )
}

function ParameterField({
  field,
  fieldId,
  onChange,
  value,
}: {
  field: PluginFormField
  fieldId: string
  onChange: (value: JsonValue) => void
  value: JsonValue | undefined
}) {
  const label = (
    <Label htmlFor={`plugin-field-${fieldId}`}>
      {field.label}
      {field.required ? <span className="ml-1 text-destructive">*</span> : null}
    </Label>
  )
  const stringValue =
    typeof value === "string" || typeof value === "number" ? String(value) : ""

  if (field.widget === "switch") {
    return (
      <div className="flex items-center justify-between gap-4">
        <div>
          {label}
          <p className="mt-1 text-xs text-muted-foreground">
            {value === true ? "已启用" : "未启用"}
          </p>
        </div>
        <Button
          onClick={() => onChange(value !== true)}
          size="sm"
          variant={value === true ? "secondary" : "outline"}
        >
          {value === true ? "开启" : "关闭"}
        </Button>
      </div>
    )
  }

  if (field.widget === "select" || field.widget === "radio") {
    return (
      <div className="grid gap-2">
        {label}
        <Select
          onValueChange={(raw) => {
            if (raw !== null) onChange(JSON.parse(raw) as JsonValue)
          }}
          value={value === undefined ? undefined : JSON.stringify(value)}
        >
          <SelectTrigger id={`plugin-field-${fieldId}`}>
            <SelectValue placeholder={field.placeholder || "请选择"} />
          </SelectTrigger>
          <SelectContent>
            {field.allow_empty ? (
              <SelectItem value="null">不设置</SelectItem>
            ) : null}
            {field.options?.map((option) => (
              <SelectItem
                key={JSON.stringify(option.value)}
                value={JSON.stringify(option.value)}
              >
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    )
  }

  if (field.widget === "checkbox_group") {
    const selected = Array.isArray(value) ? value : []
    return (
      <div className="grid gap-2">
        {label}
        <div className="flex flex-wrap gap-2">
          {field.options?.map((option) => {
            const key = JSON.stringify(option.value)
            const active = selected.some((item) => JSON.stringify(item) === key)
            return (
              <Button
                key={key}
                onClick={() =>
                  onChange(
                    active
                      ? selected.filter((item) => JSON.stringify(item) !== key)
                      : [...selected, option.value]
                  )
                }
                size="sm"
                variant={active ? "secondary" : "outline"}
              >
                {option.label}
              </Button>
            )
          })}
        </div>
      </div>
    )
  }

  if (field.widget === "list") {
    return (
      <ListField
        field={field}
        fieldId={fieldId}
        label={label}
        onChange={onChange}
        value={value}
      />
    )
  }

  if (field.widget === "textarea") {
    return (
      <div className="grid gap-2">
        {label}
        <Textarea
          id={`plugin-field-${fieldId}`}
          onChange={(event) => onChange(event.target.value)}
          placeholder={field.placeholder}
          value={stringValue}
        />
      </div>
    )
  }

  return (
    <div className="grid gap-2">
      {label}
      <Input
        id={`plugin-field-${fieldId}`}
        onChange={(event) =>
          onChange(
            field.type === "number" || field.type === "integer"
              ? Number(event.target.value)
              : event.target.value
          )
        }
        placeholder={field.placeholder}
        type={
          field.type === "number" ||
          field.type === "integer" ||
          field.widget === "number"
            ? "number"
            : "text"
        }
        value={stringValue}
      />
    </div>
  )
}

function ListField({
  field,
  fieldId,
  label,
  onChange,
  value,
}: {
  field: PluginFormField
  fieldId: string
  label: React.ReactNode
  onChange: (value: JsonValue) => void
  value: JsonValue | undefined
}) {
  const items = Array.isArray(value) ? value : []
  const itemSchema = field.items
  if (!itemSchema) return null
  const addItem = () =>
    onChange([
      ...items,
      itemSchema.type === "object"
        ? Object.fromEntries(
            Object.entries(itemSchema.properties ?? {}).map(
              ([key, property]) => [key, property.default ?? ""]
            )
          )
        : itemSchema.type === "number" || itemSchema.type === "integer"
          ? 0
          : "",
    ])
  return (
    <div className="grid gap-2">
      {label}
      <div className="space-y-2">
        {items.map((item, index) => (
          <div className="flex gap-2" key={index}>
            {itemSchema.type === "object" &&
            typeof item === "object" &&
            item !== null &&
            !Array.isArray(item) ? (
              <div className="grid flex-1 gap-2 sm:grid-cols-2">
                {Object.entries(itemSchema.properties ?? {}).map(
                  ([key, property]) => (
                    <ParameterField
                      field={property}
                      fieldId={`${fieldId}-${index}-${key}`}
                      key={key}
                      onChange={(next) => {
                        const nextItems = [...items]
                        nextItems[index] = { ...item, [key]: next }
                        onChange(nextItems)
                      }}
                      value={item[key]}
                    />
                  )
                )}
              </div>
            ) : (
              <Input
                className="flex-1"
                onChange={(event) => {
                  const nextItems = [...items]
                  nextItems[index] =
                    itemSchema.type === "number" ||
                    itemSchema.type === "integer"
                      ? Number(event.target.value)
                      : event.target.value
                  onChange(nextItems)
                }}
                value={
                  typeof item === "string" || typeof item === "number"
                    ? String(item)
                    : ""
                }
              />
            )}
            <Button
              aria-label="删除列表项"
              onClick={() =>
                onChange(items.filter((_, itemIndex) => itemIndex !== index))
              }
              size="icon"
              variant="ghost"
            >
              <Minus />
            </Button>
          </div>
        ))}
      </div>
      <Button className="w-fit" onClick={addItem} size="sm" variant="outline">
        <Plus />
        添加项目
      </Button>
    </div>
  )
}
