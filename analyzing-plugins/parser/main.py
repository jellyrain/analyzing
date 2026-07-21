from analyzing.build_kit import build_plugin_package
from analyzing.test import run_plugin_sample


# result = run_plugin_sample(
#     text="""到达导管室时间：2026年06月15日18时09分         开始穿刺时间：2026年06月15日18时16分
# 穿刺成功时间：2026年06月15日18时17分           开始造影时间：2026年06月15日18时18分
# 造影结束时间：2026年06月15日18时21分           导丝通过时间：2026年06月15日18时29分""",
#     params={},
#     project_dir="parser/str_time_parser",
# )


build_plugin_package(project_dir="parser/auto_kv_parser", output_dir="dist")
build_plugin_package(project_dir="parser/bracket_kv_parser", output_dir="dist")
build_plugin_package(project_dir="parser/choice_parser", output_dir="dist")
build_plugin_package(project_dir="parser/regex_parser", output_dir="dist")
build_plugin_package(project_dir="parser/str_number_parser", output_dir="dist")
build_plugin_package(project_dir="parser/str_time_parser", output_dir="dist")
build_plugin_package(project_dir="parser/time_parser", output_dir="dist")
