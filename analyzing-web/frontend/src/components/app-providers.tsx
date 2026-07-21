import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

type AppProvidersProps = {
  children: ReactNode
}

/** 集中挂载所有应用级 Provider，后续增加 Toast 等能力无需修改入口。 */
export function AppProviders({ children }: AppProvidersProps) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
