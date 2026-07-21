# roam-code 扩展集成模式

本文件记录在 roam-code 上扩展业务规则模块时学到的模式，避免重复踩坑。

## 1. CLI 命令注册

在 `src/roam/cli.py` 的 `_COMMANDS` 字典中添加：

```python
_COMMANDS = {
    ...
    "business-rules-extract": (
        "roam.business_rules.commands.cmd_br_extract", "cmd_br_extract",
    ),
}
```

格式: `"命令名": ("模块路径", "函数名")`。roam 使用 LazyGroup 懒加载，只在用户实际执行时才 import。

## 2. MCP 工具注册

在 `src/roam/mcp_server.py` 中：

```python
@_tool(name="business_rules_extract", description="从 Java 代码提取业务规则(AST引擎)")
def business_rules_extract(update: bool = False, root: str = ".") -> dict:
    args = ["business-rules-extract", "--json"]
    if update:
        args.append("--update")
    return _run_roam(args, root)
```

然后加入 `_WORKFLOW_TOOLS` 集合让工具在所有预设中可用。

## 3. DB Schema 扩展

在 `src/roam/db/schema.py` 的 `SCHEMA_SQL = """..."""` 字符串末尾（`"""` 之前）追加新表的 SQL。使用 `CREATE TABLE IF NOT EXISTS` 确保幂等。

**关键:** `SCHEMA_SQL` 是一个 Python 三引号字符串，新 SQL 必须加在 `"""` 之前，不能破坏字符串结构。

## 4. ⚠️ CLI 命令必须懒加载 import（CI 崩溃教训）

**错误做法:**
```python
# cmd_br_extract.py — 模块顶层导入
from roam.business_rules.extractor import BusinessRuleExtractor  # ❌ 导致 pip install 崩溃
```

**正确做法:**
```python
@click.command("business-rules-extract")
def cmd_br_extract(...):
    from roam.business_rules.extractor import BusinessRuleExtractor  # ✅ 懒加载
```

原因: roam-code 的 `_COMMANDS` 在模块加载时引用我们的模块路径。如果我们的模块有顶层 import，那些 import 在 pip install 时就会被触发，依赖缺失会导致整个包安装失败，CI 全灭。

**同样适用:** `_get_db_path()` 中的 `find_project_root` 也必须懒加载：
```python
def _get_db_path():
    try:
        from roam.db.connection import find_project_root  # ✅ 懒加载
        root = find_project_root()
    except Exception:
        root = "."
    return f"{root}/.roam/index.db"
```

## 5. SVN 兼容

roam-code 使用文件 mtime 检测变更，不依赖 git。`extract --update` 比较 `files` 表的 `mtime` 与当前文件时间戳。

快照的 `git_commit` 字段为空时用 `--label` 替代。

## 6. conflict.py 的 _auth_removed 陷阱

`business-rules extract` 执行 `DELETE FROM business_rules WHERE 1=1`（清表重建）。因此 `_auth_removed` 不能查当前 `business_rules` 表找被删规则——已经被清掉了。

正确做法: 从快照的 `removed_rules` JSON 字段中提取 rule_id，与上一快照的 `added_rules` 交叉比对，找到曾在上一版本中存在但当前已不在的 AUTHORIZATION 类型规则。
