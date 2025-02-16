import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "flask", "sqlite3"],
    "excludes": [],
    "include_files": [
        ("templates", "templates"),
        ("static", "static"),
        ("terms.db", "terms.db")
    ]
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="تطبيق المصطلحات التقنية",
    version="1.0",
    description="تطبيق المصطلحات التقنية",
    options={"build_exe": build_exe_options},
    executables=[Executable("app.py", base=base, target_name="تطبيق المصطلحات التقنية.exe")]
)
