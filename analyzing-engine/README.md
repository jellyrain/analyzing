按你现在这套 src/... 结构，引擎实现顺序我建议就固定成 7 步，别乱跳：
配置层
先做 src/app/config.py。
把 [config/engine.toml](F:/project/analyzing/analyzing_doc/analyzing-engine/config/engine.toml) 读取、校验、转成模型，顺手把路径标准化。
先别碰插件调用，先保证引擎启动时“知道自己是谁、插件目录在哪、remote 策略是什么”。

启动骨架
做 src/app/bootstrap.py 和 [main.py](F:/project/analyzing/analyzing_doc/analyzing-engine/main.py)。
目标只有一个：引擎能正常启动，并拿到完整 EngineConfig 和一个全局上下文。
这一步先不要求真正加载插件。

HTTP 入口
做 src/api/http.py。
先只放最小接口：
/healthz
/system/info
/plugins
remote 注册相关占位接口

这样后面你做 remote 时不用再反过来改启动骨架。
插件清单与扫描
做 src/registry/manifest.py 和 src/registry/catalog.py。
这里负责：扫描 plugins/biz、plugins/infra
读取 manifest
校验 SDK 兼容性
区分 inproc / subprocess / remote
建立内存注册表

这一步只做“发现和登记”，先不要真的执行插件。
inproc 运行时
做 src/runtime/inproc.py。
这是第一优先运行方式，因为最简单、最容易打通全链路。
先把 biz 的解析器、切分器通过 import 跑起来，引擎主流程先只支持 inproc。

infra 接入
做 src/infra/...。
先把存储这类基础设施插件接进来，让引擎启动时能选定一个 infra.storage。
这里重点不是花哨，而是先把“引擎依赖哪个基础设施插件”这件事走通。

remote 然后 subprocess
最后再做：
remote 注册表维护、租约过期、引擎调用 remote 插件
subprocess 拉起、本地进程管理、超时和关闭

顺序必须是 remote 在前，subprocess 在后。
因为 remote 只是多一条网络调用链，subprocess 还要多一层进程生命周期管理，复杂度更高。
如果你要更具体一点，第一周就按这个最小落地批次开：
src/app/config.py
src/app/bootstrap.py
src/api/http.py
src/registry/manifest.py
src/registry/catalog.py
src/runtime/inproc.py
这 6 个出来以后，引擎就已经不是空壳了，至少能：
启动
读配置
扫插件
列插件
跑 inproc 插件
然后第二批再做：
src/runtime/remote.py
src/runtime/subprocess.py
src/infra/storage.py
src/obs/logging.py
如果你愿意，我下一条直接给你“第一批 6 个文件分别放什么类、什么函数、什么字段”。
