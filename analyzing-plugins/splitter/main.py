from analyzing.build_kit import build_plugin_package
from analyzing.test import run_plugin_sample

# result = run_plugin_sample(
#     """关键时间点：
# 到达导管室时间：2026年06月15日18时09分         开始穿刺时间：2026年06月15日18时16分
# 穿刺成功时间：2026年06月15日18时17分           开始造影时间：2026年06月15日18时18分
# 造影结束时间：2026年06月15日18时21分           导丝通过时间：2026年06月15日18时29分
# """,
#     {},
#     project_dir="splitter/line_splitter",
# )
#
# print(result)

build_plugin_package(project_dir="splitter/anchor_splitter", output_dir="dist")
build_plugin_package(project_dir="splitter/line_splitter", output_dir="dist")
build_plugin_package(project_dir="splitter/paragraph_splitter", output_dir="dist")
build_plugin_package(project_dir="splitter/regex_splitter", output_dir="dist")
build_plugin_package(project_dir="splitter/sentence_splitter", output_dir="dist")
build_plugin_package(project_dir="splitter/window_splitter", output_dir="dist")