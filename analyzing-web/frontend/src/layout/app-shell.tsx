import { Activity, SlidersHorizontal, Workflow } from "lucide-react"
import { Link, NavLink } from "react-router"

import { ThemeToggle } from "@/components/theme-toggle"

type AppShellProps = {
  activePage?: "monitor" | "rules" | "settings"
  children: React.ReactNode
  /** 页面自行管理局部滚动时，禁止应用壳产生整页滚动条。 */
  contentScrollable?: boolean
}

/** 已连接 Engine 后的应用骨架，规则、监控和设置共用同一层级与导航。 */
export function AppShell({
  activePage = "settings",
  children,
  contentScrollable = true,
}: AppShellProps) {
  const monitorNavigationClassName = ({ isActive }: { isActive: boolean }) =>
    isActive
      ? "flex h-8 items-center rounded-md pl-5 text-xs font-medium text-sidebar-foreground"
      : "flex h-8 items-center rounded-md pl-5 text-xs text-muted-foreground transition-colors hover:text-sidebar-foreground"

  return (
    <div className="flex h-svh overflow-hidden bg-background text-foreground">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar/72 px-3 py-4 backdrop-blur-xl lg:flex">
        <Link
          className="flex items-center gap-3 rounded-lg px-3 py-2"
          to="/settings"
        >
          <span className="grid size-8 place-items-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
            A
          </span>
          <span className="min-w-0 leading-tight">
            <strong className="block text-sm tracking-[0.08em]">
              ANALYZING
            </strong>
            <span className="mt-1 block text-xs text-muted-foreground">
              文档解析工作台
            </span>
          </span>
        </Link>

        <div className="mt-10 px-3 text-[0.68rem] font-semibold tracking-[0.14em] text-muted-foreground">
          WORKSPACE
        </div>
        <nav className="mt-2 grid gap-1" aria-label="主导航">
          <Link
            className={
              activePage === "rules"
                ? "flex h-10 items-center gap-2 rounded-lg bg-sidebar-accent px-3 text-sm font-medium text-sidebar-accent-foreground"
                : "flex h-10 items-center gap-2 rounded-lg px-3 text-sm text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            }
            to="/rules"
          >
            <Workflow className="size-4" />
            规则配置
          </Link>
          <Link
            className={
              activePage === "monitor"
                ? "flex h-10 items-center gap-2 rounded-lg bg-sidebar-accent px-3 text-sm font-medium text-sidebar-accent-foreground"
                : "flex h-10 items-center gap-2 rounded-lg px-3 text-sm text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            }
            to="/monitor/overview"
          >
            <Activity className="size-4" />
            运行监控
          </Link>
          {activePage === "monitor" ? (
            <div
              className="relative ml-6 grid gap-0.5 py-1 before:absolute before:top-1 before:bottom-1 before:left-1.5 before:w-px before:bg-sidebar-border"
              aria-label="运行监控子导航"
            >
              <NavLink
                className={monitorNavigationClassName}
                to="/monitor/overview"
              >
                运行总览
              </NavLink>
              <NavLink
                className={monitorNavigationClassName}
                to="/monitor/invocations"
              >
                调用记录
              </NavLink>
              <NavLink
                className={monitorNavigationClassName}
                to="/monitor/plugins"
              >
                插件状态
              </NavLink>
            </div>
          ) : null}
          <Link
            className={
              activePage === "settings"
                ? "flex h-10 items-center gap-2 rounded-lg bg-sidebar-accent px-3 text-sm font-medium text-sidebar-accent-foreground"
                : "flex h-10 items-center gap-2 rounded-lg px-3 text-sm text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            }
            to="/settings"
          >
            <SlidersHorizontal className="size-4" />
            系统配置
          </Link>
        </nav>

        <div className="mt-auto border-t border-sidebar-border px-3 pt-4 text-xs leading-5 text-muted-foreground">
          <p className="flex items-center gap-2 text-sidebar-foreground">
            <span className="size-1.5 rounded-full bg-primary" />
            LOCAL HOST ONLINE
          </p>
          <p className="mt-2">已连接到当前 Engine</p>
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center border-b border-border bg-background/72 px-4 backdrop-blur-xl sm:px-7">
          <div className="min-w-0">
            <p className="text-xs font-semibold tracking-[0.14em] text-primary">
              ANALYZING WEB
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              本地 Host 工作区
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="hidden rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary sm:inline-flex">
              ENGINE CONNECTED
            </span>
            <ThemeToggle />
          </div>
        </header>
        <main
          className={`min-h-0 flex-1 ${contentScrollable ? "overflow-auto" : "overflow-hidden"}`}
        >
          {children}
        </main>
      </section>
    </div>
  )
}
