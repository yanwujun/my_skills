#!/usr/bin/env python3
"""
递归补齐 Maven 仓库中所有缺失的 parent POM。

用法：
  python3 resolve_parent_poms.py <target_repo> <source_repo>

说明：
  dependency:list/dependency:tree 只显示 jar 依赖，而 Maven 编译还需要
  所有 <parent> 链（父POM → 祖父POM → ...）。这些永远不会出现在
  依赖树输出中，必须从源仓库递归补齐。

典型结果：478 个 jar 依赖 → 递归补齐至约 676 个 artifact（约 +200 个 parent POM）
"""

import os
import re
import shutil
import sys


def get_copied_artifacts(repo_path):
    """返回目标中所有已存在的 (group, artifact, version)"""
    copied = set()
    for root, dirs, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".pom"):
                rel = os.path.relpath(root, repo_path)
                parts = rel.split(os.sep)
                if len(parts) >= 3:
                    group = ".".join(parts[:-2])
                    artifact = parts[-2]
                    version = parts[-1]
                    copied.add((group, artifact, version))
    return copied


def main():
    if len(sys.argv) != 3:
        print("用法: python3 resolve_parent_poms.py <target_repo> <source_repo>")
        sys.exit(1)

    target_repo = sys.argv[1].rstrip("/")
    source_repo = sys.argv[2].rstrip("/")

    if not os.path.isdir(target_repo):
        print(f"❌ 目标仓库不存在: {target_repo}")
        sys.exit(1)
    if not os.path.isdir(source_repo):
        print(f"❌ 源仓库不存在: {source_repo}")
        sys.exit(1)

    copied_set = get_copied_artifacts(target_repo)
    initial_count = len(copied_set)
    missing_stack = set(copied_set)
    to_process = list(copied_set)

    total_copied = 0
    round_num = 0

    while to_process:
        round_num += 1
        new_parents = set()

        for group, artifact, version in to_process:
            dir_path = os.path.join(
                target_repo, group.replace(".", "/"), artifact, version
            )
            if not os.path.isdir(dir_path):
                continue
            pom_files = [f for f in os.listdir(dir_path) if f.endswith(".pom")]
            if not pom_files:
                continue

            pom_path = os.path.join(dir_path, pom_files[0])
            try:
                with open(pom_path, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except Exception:
                continue

            for m in re.finditer(
                r"<parent>\s*<groupId>([^<]+)</groupId>\s*"
                r"<artifactId>([^<]+)</artifactId>\s*"
                r"<version>([^<]+)</version>",
                content,
                re.DOTALL,
            ):
                pg, pa, pv = (
                    m.group(1).strip(),
                    m.group(2).strip(),
                    m.group(3).strip(),
                )
                key = (pg, pa, pv)
                if key not in missing_stack:
                    missing_stack.add(key)
                    new_parents.add(key)

        if not new_parents:
            print(f"  → 第 {round_num} 轮: 无新增，解析完成 ✓")
            break

        copied_this_round = 0
        missing_this_round = 0
        for pg, pa, pv in sorted(new_parents):
            src_dir = os.path.join(
                source_repo, pg.replace(".", "/"), pa, pv
            )
            dst_dir = os.path.join(
                target_repo, pg.replace(".", "/"), pa, pv
            )
            if os.path.isdir(src_dir):
                os.makedirs(dst_dir, exist_ok=True)
                for f in os.listdir(src_dir):
                    sf = os.path.join(src_dir, f)
                    df = os.path.join(dst_dir, f)
                    if os.path.isfile(sf) and not os.path.exists(df):
                        shutil.copy2(sf, df)
                        copied_this_round += 1
            else:
                missing_this_round += 1

        total_copied += copied_this_round
        print(
            f"  → 第 {round_num} 轮: {len(new_parents)} 个 parent POM "
            f"(已复制 {copied_this_round} files"
            + (f", {missing_this_round} 个源不存在)" if missing_this_round else ")")
        to_process = list(new_parents)

    final_count = len(get_copied_artifacts(target_repo))
    print(f"\n✅ parent POM 递归解析完成")
    print(f"   初始 artifact 数: {initial_count}")
    print(f"   最终 artifact 数: {final_count}")
    print(f"   新增: {final_count - initial_count}")

    # 总文件数
    total_files = sum(len(files) for _, _, files in os.walk(target_repo))
    total_size = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, dn, filenames in os.walk(target_repo)
        for f in filenames
    )
    print(f"   总文件数: {total_files}")
    print(f"   总大小: {total_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
