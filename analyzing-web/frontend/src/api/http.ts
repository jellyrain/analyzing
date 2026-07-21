import axios from "axios"

/** Web 页面只请求本地 Host，由 Host 负责转发 Engine 请求。 */
export const http = axios.create({
  baseURL: "/api",
  timeout: 15_000,
})

/** 将 Host 返回的常见错误结构转换为可直接展示的中文提示。 */
export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) {
    return fallback
  }

  const detail = error.response?.data?.detail
  if (typeof detail === "string") {
    return detail
  }

  if (typeof error.response?.data?.message === "string") {
    return error.response.data.message
  }

  return error.message || fallback
}
