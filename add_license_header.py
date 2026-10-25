#!/usr/bin/env python3
import os

# ========== 配置区 修改这里 ==========
# Python文件注释模板
PY_HEADER = '''# CrossVideo — Cross‑platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''

# JS / TS / Vue 文件注释模板
JS_HEADER = '''/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

'''

# 需要处理的后缀
SUFFIX_PY = {".py"}
SUFFIX_JS = {".js", ".ts", ".vue"}

# 需要跳过的目录（不会遍历这些文件夹）
SKIP_DIRS = {
    ".git", "venv", ".venv", "node_modules", "dist", "build", "__pycache__",
    ".pytest_cache", "postgres-data", "tampermonkey", ".husky"
}
# ====================================


def has_already_header(content, header_snippet):
    """简单检测是否已经添加过头部，避免重复插入"""
    snippet = header_snippet.splitlines()[0]
    return snippet in content[:1000]


def process_file(filepath, suffix):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if suffix in SUFFIX_PY:
        header = PY_HEADER
    elif suffix in SUFFIX_JS:
        header = JS_HEADER
    else:
        return

    if has_already_header(content, header):
        print(f"跳过(已有头部): {filepath}")
        return

    # 处理 python shebang #! 保留在最顶部
    if suffix == ".py" and content.startswith("#!"):
        lines = content.splitlines(keepends=True)
        shebang = lines[0]
        rest = "".join(lines[1:])
        new_content = shebang + "\n" + header + rest
    else:
        new_content = header + content

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"已处理: {filepath}")


def walk(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 删除跳过目录，os.walk就不会进去遍历
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            _, ext = os.path.splitext(fname)
            if ext in SUFFIX_PY or ext in SUFFIX_JS:
                fullpath = os.path.join(dirpath, fname)
                process_file(fullpath, ext)


if __name__ == "__main__":
    walk(".")
