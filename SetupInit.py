from cx_Freeze import setup, Executable

# 设置你的程序名称和版本
program_name = "Cloud Init for Pika Cloud"
program_version = "0.1"

# 指定你的主程序文件
main_script = "CloudInit.py"

# 配置 cx_Freeze
setup(
    name=program_name,
    version=program_version,
    description="Cloud Init for Pika Cloud",
    executables=[Executable(main_script)],
    options={
        "build_exe": {
            # 包含的文件和模块
            "include_files": [],
            "includes": [],
            # 排除的文件和模块
            "excludes": [],
            # 目标平台（可选，通常自动检测）
        }
    }
)