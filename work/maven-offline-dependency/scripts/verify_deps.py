#!/usr/bin/env python3
"""
验证 Maven 依赖仓库是否包含 dependency:list 中声明的所有 jar。

用法:
  python3 scripts/verify_deps.py <仓库目录> <dependency-list.txt> [依赖列表2 ...]

示例:
  python3 scripts/verify_deps.py /tmp/mallrepository /tmp/malltrade-dependency-list.txt
  python3 scripts/verify_deps.py /tmp/mallrepository /tmp/malltrade-dependency-list.txt /mnt/d/mallbase-dep-list.txt

返回码: 0 = 全部匹配, 1 = 有缺失
"""
import re
import os
import sys


def parse_dep_list(filepath: str) -> set[tuple[str, str, str]]:
    """
    解析 mvn dependency:list 的输出。

    支持两种格式:
      1. standard:  com.gec:gec-org-core:jar:1.18.0:compile
      2. 带缩进:    |  +- com.gec:gec-org-core:jar:1.18.0:compile
    """
    deps = set()
    # 匹配 group:artifact:jar:version:scope
    # group 可以包含 dots, artifact 可以是字母数字下划线横线
    # version 可以包含字母数字下划线横线点号
    pattern = re.compile(
        r'([\w._-]+(?:\.[\w._-]+)*):'   # groupId
        r'([\w._-]+):'                    # artifactId
        r'jar:'                            # packaging
        r'([\w._-]+[\w._-]*)'            # version
        r':(compile|runtime|test|provided|system)'  # scope
    )

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            m = pattern.search(line)
            if m:
                deps.add((m.group(1), m.group(2), m.group(3)))

    return deps


def build_existing_set(repo_dir: str) -> set[tuple[str, str, str]]:
    """从仓库目录结构构建 (gid, aid, ver) 集合"""
    existing = set()
    if not os.path.isdir(repo_dir):
        return existing

    for root, dirs, files in os.walk(repo_dir):
        for f in files:
            if not f.endswith('.jar'):
                continue
            rel = os.path.relpath(os.path.join(root, f), repo_dir)
            parts = rel.split(os.sep)
            if len(parts) < 4:
                continue  # 结构至少是 group/.../artifact/version/jar
            aid = parts[-3]
            ver = parts[-2]
            gid = '.'.join(parts[:-3])
            existing.add((gid, aid, ver))

    return existing


def main():
    if len(sys.argv) < 3:
        print("用法: python3 verify_deps.py <仓库目录> <dependency-list.txt> [依赖列表2 ...]")
        sys.exit(1)

    repo_dir = sys.argv[1]
    dep_files = sys.argv[2:]

    if not os.path.isdir(repo_dir):
        print(f"❌ 仓库目录不存在: {repo_dir}")
        sys.exit(1)

    # 解析所有依赖列表
    all_deps: set[tuple[str, str, str]] = set()
    for f in dep_files:
        if not os.path.isfile(f):
            print(f"⚠️ 依赖列表文件不存在: {f}，跳过")
            continue
        deps = parse_dep_list(f)
        print(f"  {os.path.basename(f)}: {len(deps)} 个依赖")
        all_deps.update(deps)

    if not all_deps:
        print("❌ 没有解析到任何依赖！请检查 dependency:list 文件格式。")
        sys.exit(1)

    print(f"\n总依赖数 (去重后): {len(all_deps)}")

    # 扫描仓库
    existing = build_existing_set(repo_dir)
    print(f"仓库中 jar 数:   {len(existing)}")

    # 对比
    missing = []
    for gid, aid, ver in sorted(all_deps):
        if (gid, aid, ver) not in existing:
            missing.append((gid, aid, ver))

    if missing:
        print(f"\n❌ 缺失 {len(missing)}/{len(all_deps)} 个依赖:\n")
        for gid, aid, ver in missing:
            path = f"{gid.replace('.', '/')}/{aid}/{ver}/{aid}-{ver}.jar"
            print(f"  MISSING: {path}")

        # 提供修复建议
        print("\n--- 修复方法 ---")
        print(f"从本地 ~/.m2/repository/ 或 D:\\apache-maven\\localRepository3.6.3 复制:")
        repo_base = "/mnt/d/apache-maven/localRepository3.6.3"
        for gid, aid, ver in missing:
            path = f"{gid.replace('.', '/')}/{aid}/{ver}"
            print(
                f"  mkdir -p {repo_dir}/{path} && "
                f"cp {repo_base}/{path}/{aid}-{ver}.jar {repo_dir}/{path}/"
            )
        sys.exit(1)
    else:
        print(f"\n✅ ALL 100%! 所有 {len(all_deps)} 个依赖都已存在于 {repo_dir}")
        sys.exit(0)


if __name__ == "__main__":
    main()
