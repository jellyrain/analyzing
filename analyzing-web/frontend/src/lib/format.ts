/**
 * 将 Engine 返回的时间统一转换为本地可读格式，避免不同页面各自使用区域化格式。
 */
export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "--"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "--"
  }

  const pad = (number: number) => String(number).padStart(2, "0")

  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
  ].join("-") + ` ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}
