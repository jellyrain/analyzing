from analyzing.build_kit import (
    build_engine_package,
    copy_release_resource,
)

build_engine_package()
copy_release_resource("static", "dist/engine", "static")

# copy_engine_dist_info(r"D:\porject_new_2026\analyzing_doc\analyzing-engine\dist\engine")
