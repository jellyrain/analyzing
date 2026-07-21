import { http } from "@/api/http"

type EngineResponse<T> = {
  code: number
  message: string
  data: T
}

/** 将一条临时规则配置提交给 Engine 执行，不依赖规则 CRUD。 */
export async function runProcessor(
  text: string,
  config: Record<string, unknown>
) {
  const response = await http.post<EngineResponse<unknown>>(
    "/engine/processor",
    {
      text,
      config,
    }
  )

  if (response.data.code !== 200) {
    throw new Error(response.data.message)
  }

  return response.data.data
}
