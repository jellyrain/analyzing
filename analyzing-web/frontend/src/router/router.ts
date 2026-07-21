import { createBrowserRouter, redirect } from "react-router"

/**
 * 路由使用对象配置集中声明。后续规则、监控页面在这里追加即可，
 * 不在路由文件中编写 JSX 或请求状态 UI。
 */
export const router = createBrowserRouter([
  {
    path: "/",
    lazy: async () => {
      const { SettingsPage } = await import("@/pages/settings/page")
      return { Component: SettingsPage }
    },
  },
  {
    path: "/settings",
    lazy: async () => {
      const { SettingsPage } = await import("@/pages/settings/page")
      return { Component: SettingsPage }
    },
  },
  {
    path: "/rules",
    lazy: async () => {
      const { RulesPage } = await import("@/pages/rules/page")
      return { Component: RulesPage }
    },
  },
  {
    path: "/monitor",
    lazy: async () => {
      const { MonitorLayout } = await import("@/pages/monitor/layout")
      return { Component: MonitorLayout }
    },
    children: [
      {
        index: true,
        loader: () => redirect("/monitor/overview"),
      },
      {
        path: "overview",
        lazy: async () => {
          const { MonitorOverviewPage } =
            await import("@/pages/monitor/overview/page")
          return { Component: MonitorOverviewPage }
        },
      },
      {
        path: "invocations",
        lazy: async () => {
          const { MonitorInvocationsPage } =
            await import("@/pages/monitor/invocations/page")
          return { Component: MonitorInvocationsPage }
        },
      },
      {
        path: "plugins",
        lazy: async () => {
          const { MonitorPluginsPage } =
            await import("@/pages/monitor/plugins/page")
          return { Component: MonitorPluginsPage }
        },
      },
    ],
  },
  {
    path: "*",
    lazy: async () => {
      const { NotFoundPage } = await import("@/pages/common/not-found-page")
      return { Component: NotFoundPage }
    },
  },
])
