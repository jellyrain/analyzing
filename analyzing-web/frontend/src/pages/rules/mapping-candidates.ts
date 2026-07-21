export type MappingCandidate = {
  alias: string
  path: string
  preview: string
}

/** 从 Engine 的 parsed 结果中提取叶子值，为字段映射生成可选 JSONPath。 */
export function buildMappingCandidates(parsed: unknown): MappingCandidate[] {
  const candidates: MappingCandidate[] = []
  collectLeafCandidates(parsed, [], candidates)
  return candidates
}

function collectLeafCandidates(
  value: unknown,
  parts: Array<number | string>,
  candidates: MappingCandidate[]
) {
  if (Array.isArray(value)) {
    value.forEach((item, index) =>
      collectLeafCandidates(item, [...parts, index], candidates)
    )
    return
  }
  if (typeof value === "object" && value !== null) {
    Object.entries(value).forEach(([key, child]) =>
      collectLeafCandidates(child, [...parts, key], candidates)
    )
    return
  }
  if (parts.length === 0) return
  const alias = [...parts].reverse().find((part) => typeof part === "string")
  candidates.push({
    alias: typeof alias === "string" ? alias : "field",
    path: buildJsonPath(parts),
    preview: formatPreview(value),
  })
}

function buildJsonPath(parts: Array<number | string>) {
  return parts.reduce<string>(
    (path, part) =>
      typeof part === "number"
        ? `${path}[${part}]`
        : `${path}["${part.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"]`,
    "$"
  )
}

function formatPreview(value: unknown) {
  const text = value === null ? "null" : String(value)
  return text.length > 48 ? `${text.slice(0, 45)}...` : text
}
