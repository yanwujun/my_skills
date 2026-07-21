#!/usr/bin/env python3
"""
检查 Maven 本地仓库中所有 POM 的 BOM import 是否完整。

BOM import 格式：
  <dependency><groupId>...</groupId><artifactId>...</artifactId>
  <version>...</version><type>pom</type><scope>import</scope></dependency>

扫描目标仓库中所有 POM，找出通过 BOM import 引用的 artifact，
检查它们是否也存在于目标仓库中（或源仓库中）。
"""

import os
import re
import sys


def main():
    if len(sys.argv) not in (2, 3):
        print("用法: python3 check_bom_imports.py <target_repo> [source_repo]")
        print("  不提供 source_repo 时只列出缺失的 BOM")
        print("  提供 source_repo 时还会检查源仓库是否存在对应的目录")
        sys.exit(1)

    target_repo = sys.argv[1].rstrip("/")
    source_repo = sys.argv[2].rstrip("/") if len(sys.argv) == 3 else None

    if not os.path.isdir(target_repo):
        print(f"❌ 目标仓库不存在: {target_repo}")
        sys.exit(1)

    bom_imports = {}

    for root, dirs, files in os.walk(target_repo):
        for f in files:
            if not f.endswith(".pom"):
                continue
            pom_path = os.path.join(root, f)
            try:
                with open(pom_path, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except Exception:
                continue

            for m in re.finditer(
                r"<dependency>\s*<groupId>([^<]+)</groupId>\s*"
                r"<artifactId>([^<]+)</artifactId>\s*"
                r"<version>([^<]+)</version>\s*"
                r"<type>pom</type>\s*<scope>import</scope>",
                content,
                re.DOTALL,
            ):
                g, a, v = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
                key = f"{g}:{a}:{v}"
                # 只记录 BOM 引用，不记录 duplicate
                if key not in bom_imports:
                    bom_imports[key] = {
                        "group": g,
                        "artifact": a,
                        "version": v,
                    }

    if not bom_imports:
        print("✅ 未发现任何 BOM import 引用")
        return 0

    # 检查每个 BOM 是否在目标仓库中
    missing_boms = []
    for key, info in sorted(bom_imports.items()):
        g, a, v = info["group"], info["artifact"], info["version"]
        dst = os.path.join(target_repo, g.replace(".", "/"), a, v)
        if not os.path.isdir(dst):
            missing_boms.append(key)
            if source_repo and os.path.isdir(
                os.path.join(source_repo, g.replace(".", "/"), a, v)
            ):
                print(f"⚠️  缺失 BOM (源存在): {key}")
            elif source_repo:
                print(f"❌  缺失 BOM (源也无): {key}")
            else:
                print(f"⚠️  缺失 BOM: {key}")

    if not missing_boms:
        print(f"✅ 所有 {len(bom_imports)} 个 BOM import 已完整！")

    print(f"\n统计: {len(bom_imports)} 个 BOM import 引用, {len(missing_boms)} 个缺失")

    # 属性占位符统计提醒
    placeholder_count = sum(
        1 for key in bom_imports if "${" in key
    )
    if placeholder_count:
        print(f"   其中 {placeholder_count} 个使用了属性占位符 (${'{...}'})，")
        print(f"   这些是 Spring Boot 等父 POM 中通过 property 继承解析的，")
        print(f"   如果源仓库也没有对应目录可以忽略。")

    return len(missing_boms)


if __name__ == "__main__":
    sys.exit(main())
