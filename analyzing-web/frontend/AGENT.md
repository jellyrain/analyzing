# Analyzing Web 前端开发规范

本文档适用于 `analyzing-web/frontend`。所有新增页面、组件和接口接入均遵循以下约束。

## 基本原则

- 页面只调用本地 Web Host，不直接调用 Engine。
- 前端负责编辑体验和展示；Host 负责本地配置与代理；Engine 是业务配置、插件和监控数据的最终来源。
- 文案、注释和用户可见提示使用中文；代码标识符使用英文。
- 修改代码使用 `apply_patch`；不覆盖或回滚用户已有改动。
- 禁止出现浏览器或应用壳的整页滚动条。编辑器类页面的页面根节点必须使用 `h-full min-h-0 overflow-hidden`，仅在左侧列表、中央工作区、右侧检查器等具体内容面板中使用 `ScrollArea` 或 `overflow-auto`。

## 相关项目路径

工作区根目录：`D:\porject_new_2026\analyzing`

| 项目 | 绝对路径 | 前端开发中的用途 |
| --- | --- | --- |
| 前端应用 | `D:\porject_new_2026\analyzing\analyzing-web\frontend` | 当前 React + Vite 项目，负责页面、交互与调用 Web Host。 |
| Web Host 后端 | `D:\porject_new_2026\analyzing\analyzing-web\backend` | 提供 `/api/host/*` 本地配置接口，并将 `/api/engine/*` 转发到 Engine。 |
| Engine | `D:\porject_new_2026\analyzing\analyzing-engine` | 业务规则、处理流程、插件管理与监控数据的最终服务端实现；用于查阅真实 API、请求模型和返回结构。 |
| 插件集合 | `D:\porject_new_2026\analyzing\analyzing-plugins` | 用于查阅 `form.schema.json`、插件参数和前端动态表单所需的实际配置定义。 |
| Web 视觉原型 | `D:\porject_new_2026\analyzing\analyzing-web` | 存放 HTML 原型与视觉参考；仅用于确认产品风格和交互，不直接复制旧页面结构。 |

- 需要确认 Engine 接口、监控字段或规则模型时，优先读取 `D:\porject_new_2026\analyzing\analyzing-engine` 的实现，而不是猜测字段。
- 需要渲染插件参数时，优先读取 `D:\porject_new_2026\analyzing\analyzing-plugins` 中对应插件的 `form.schema.json`。
- 浏览器请求只能发往 Web Host 的相对地址 `/api/host/*` 和 `/api/engine/*`；即使查阅了 Engine 源码，也不能在前端直接请求 Engine。

## 组件与依赖

- 开始实现前，先检查 shadcn 是否已有对应组件。已有组件必须优先复用，不手写等价基础控件。
- shadcn 的初始化和组件添加统一使用 `npx`，例如：

  ```powershell
  npx shadcn@4.13.1 add input label
  ```

- 普通项目依赖使用 `pnpm add` / `pnpm add -D` 管理。
- `src/components/ui/` 是 shadcn 生成组件目录。除必要兼容修复外，不在其中放业务组件。
- 当前不引入 `react-hook-form`、`zod` 作为页面表单方案；Host/Engine 是配置校验的权威来源。
- 当前不引入图表库、Redux 或额外 UI 库。确有需求时先说明原因与影响。

## 目录与文件

路由页面采用“一个页面一个目录”的结构：

```text
src/pages/<page-name>/
├─ page.tsx             # 路由页面，仅负责组合视图与调用 hook
├─ types.ts             # 当前页面共享类型
├─ hooks/               # 仅 .ts，负责请求、状态与领域逻辑
└─ components/          # 当前页面专属的 .tsx 展示组件
```

- `page.tsx` 不能定义自定义 hook，不能承载 API 请求、缓存同步或复杂状态机。
- hook 必须独立放在 `hooks/*.ts`，不使用 `.tsx`。
- 可复用的加载、错误、空状态放在 `src/pages/common/`，禁止在 router 或业务页中重复手写。
- 应用级共享布局放在 `src/layout/`；跨页面基础展示组件放在 `src/components/`。
- `src/api/` 只定义 HTTP 客户端、Host API 和 Engine 代理 API，不混入页面状态。
- TanStack Query 管理服务端数据；Zustand 只管理本地 UI 状态。不要把同一份服务端数据复制到 Zustand。

## 路由

- 路由只使用 React Router 的对象配置，集中定义在 `src/router/router.ts`。
- 使用 `createBrowserRouter([...])` 与 `Component` 字段；禁止在路由文件中使用 `BrowserRouter`、`Routes`、`Route` JSX。
- 路由配置文件使用 `.ts`，不放加载、错误或空状态 JSX。
- 路由引用独立的通用状态页面，例如 `pages/common/loading-page.tsx`、`service-error-page.tsx`、`not-found-page.tsx`。
- 新增业务页前先确认 Host bootstrap：未配置 Engine 时必须引导到 `/settings`。

## API 与配置

- 所有请求基于 `src/api/http.ts` 的 Axios 实例，使用相对路径 `/api/*`。
- Host 自有接口使用 `/api/host/*`；Engine 代理接口使用 `/api/engine/*`。
- `engine_origin` 只保存根地址，例如 `http://127.0.0.1:8000`，不能包含 `/api`。
- Host 本地配置包括 Engine 地址、监控刷新等 Web 偏好；业务规则最终保存到 Engine，待 Engine CRUD 就绪后接入。
- 当前规则相关页面可使用内存草稿与空状态，但不得伪造演示规则数据或把规则持久化到 Host。

## 视觉与交互

- 产品方向：蓝白为主、低攻击性、轻量玻璃质感、中文优先；暗色模式使用深蓝灰而非纯黑反色。
- 全局颜色、圆角和明暗主题只修改 `src/index.css` 的 OKLCH 主题变量；亮色和暗色必须同时维护。
- 首次连接页、加载页、错误页和 404 复用同一套 `SetupStateShell` 视觉语言，不能出现风格断层。
- 已配置后的业务页面必须复用 `AppShell`，保持侧栏、顶部状态与主题切换一致。
- 玻璃和模糊只用于应用壳、顶栏等层级容器；不要把每个内容块都做成悬浮玻璃卡片。
- 禁止通用的指标卡片墙、重复的相同卡片网格、装饰性网格背景、渐变文字、过大的圆角和无意义的彩色侧边线。
- 桌面工作区默认占满可视区，滚动发生在明确的内容容器内，避免整页无控制地溢出。
- 表单结果、连接状态等重要反馈优先显示在原上下文中；不要只使用短暂消失的 Toast。
- 所有可点击控件有可见焦点态、禁用态和中文 `aria-label` / `title`（图标按钮尤其需要）。

## 验证

每次完成前至少执行：

```powershell
pnpm lint
```

- 页面交互、真实 Host/Engine 联调由用户在本地运行环境验证时，不要擅自覆盖其本地配置。
- 如果未执行某项验证，必须在交付说明中明确指出。
