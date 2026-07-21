#!/usr/bin/env python3
"""
Parse mvn dependency:tree output and copy all artifacts to target Maven repo.
Preserves full directory structure (groupId/artifactId/version/).

Usage:
    python3 parse-deps-tree-and-copy.py <deps-file> <source-repo> <target-repo>

Example:
    python3 parse-deps-tree-and-copy.py \
        /mnt/c/Users/Administrator/temp/deps.txt \
        /mnt/d/apache-maven/localRepository3.6.3 \
        /tmp/mallrepository
"""
import re
import os
import shutil
import sys
from pathlib import Path


def parse_deps(filepath):
    """Parse mvn dependency:tree output, return set of (g:a:v) tuples."""
    deps = set()
    # Pattern matches the tree format:
    #   |  +- com.gmsoft:starter-job:jar:2.2.5:compile
    #   |  |  \- org.quartz-scheduler:quartz:jar:2.3.2:compile
    #   \- com.google.code.findbugs:jsr305:jar:3.0.2:compile
    pattern = re.compile(
        r'[+\-|\\ ]+\s+([\w.]+):([\w.-]+):[\w.-]+:([\w.]+(?:-SNAPSHOT)?):'
    )

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            m = pattern.search(line)
            if m:
                g, a, v = m.group(1), m.group(2), m.group(3)
                deps.add((g, a, v))
    return deps


def copy_artifact(source_repo, target_repo, group_id, artifact_id, version):
    """Copy all files for a Maven artifact, preserving directory structure."""
    group_path = group_id.replace('.', '/')
    artifact_dir = f"{group_path}/{artifact_id}/{version}"
    source_dir = os.path.join(source_repo, artifact_dir)
    target_dir = os.path.join(target_repo, artifact_dir)

    if not os.path.isdir(source_dir):
        return None, f"MISSING: {artifact_dir}"

    os.makedirs(target_dir, exist_ok=True)

    file_count = 0
    total_size = 0
    for fname in os.listdir(source_dir):
        src = os.path.join(source_dir, fname)
        dst = os.path.join(target_dir, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            file_count += 1
            total_size += os.path.getsize(src)

    return (file_count, total_size), None


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <deps-file> <source-repo> <target-repo>")
        sys.exit(1)

    deps_file = sys.argv[1]
    source_repo = sys.argv[2]
    target_repo = sys.argv[3]

    if not os.path.isfile(deps_file):
        print(f"❌ Deps file not found: {deps_file}")
        sys.exit(1)
    if not os.path.isdir(source_repo):
        print(f"❌ Source repo not found: {source_repo}")
        sys.exit(1)

    deps = parse_deps(deps_file)
    print(f"Total unique dependencies found: {len(deps)}")

    results = []
    total_files = 0
    total_size = 0
    missing = []

    for g, a, v in sorted(deps, key=lambda x: (x[0], x[1])):
        info, err = copy_artifact(source_repo, target_repo, g, a, v)
        if err:
            missing.append(f"  {g}:{a}:{v} -> {err}")
            print(f"  ❌ {g}:{a}:{v} -> {err}")
        else:
            files, size = info
            total_files += files
            total_size += size
            print(f"  ✅ {g}:{a}:{v} ({files} files, {size/1024:.1f} KB)")
            results.append((g, a, v, files, size))

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total unique dependencies: {len(deps)}")
    print(f"Successfully copied: {len(results)}")
    print(f"Missing: {len(missing)}")
    print(f"Total files: {total_files}")
    print(f"Total size: {total_size/1024/1024:.1f} MB")

    if missing:
        print(f"\n❌ Missing dependencies:")
        for m in missing:
            print(m)

    return len(missing)


if __name__ == "__main__":
    sys.exit(main())
