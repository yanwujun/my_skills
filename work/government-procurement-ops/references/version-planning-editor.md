# 版本规划编辑器

> Absorbed from `version-planning-editor` skill. Covers creating and editing version planning
> documents for 直采商城 and 框架协议 upgrades.

## Directory Structure

Root path (WSL): `/mnt/d/项目/svn/P2040直采与框架协议/版本管理/`

### Module dirs
| Module | Path | Note |
|--------|------|------|
| 直采商城(新） | `直采商城(新）/` | v1.26.x+ (active) |
| 直采商城 | `直采商城/` | v1.24.x~v1.25.x (legacy) |
| 框架协议 | `框架协议/` | closed framework agreements |
| 协议供货 | `协议供货/` | framework supplies |

### Naming convention
```
{version} {description}/
```
Example: `1.26.3 商城优化-合同供应商编辑与商品可删除/`

### Version folder structure
```
{version} {description}/
├── 升级说明文档.md        # Functional upgrade doc
├── 升级方案.md            # New platform setup doc
├── 升级说明文档.pdf       # PDF version
├── 升级SQL/
│   ├── 1.{feature}.sql
│   └── ...
├── image-{timestamp}.png  # Screenshots
└── image-{timestamp}.png
```

## Templates

### Template A: Functional Upgrade (升级说明文档.md)

```markdown
# {version} {description} - 升级说明
---
## 一、{module_name}
**原始需求：** {description}
### 后端需求
1. {API/function}
   - **入参：** {params}
   - **鉴权：** {auth}
### 前端需求
1. **{page}** — {function}
---
## 二、{module_name}
...
---
## 三、SQL upgrades
--- sql
-- {version}
ALTER TABLE ...
---
## 四、Release
### Backend
- SVN: https://192.168.2.10:8080/svn/.../电子直采/branches/optimization
### Frontend
- SVN: https://192.168.2.10:8080/svn/.../电子直采/branches/current
```

### Template B: New Platform Setup (升级方案.md)

For new platform deployment. Includes market config, DB upgrade, Nginx config.

## Workflow

### 1. List existing versions
```bash
ls -1 "/mnt/d/项目/svn/P2040直采与框架协议/版本管理/直采商城(新）/"
ls -1 "/mnt/d/项目/svn/P2040直采与框架协议/版本管理/框架协议/"
```

### 2. Create new version
```bash
mkdir -p "/mnt/d/.../版本管理/直采商城(新）/{version} {desc}/升级SQL"
mkdir -p "/mnt/d/.../版本管理/框架协议/{version} {desc}/升级SQL"
```

### 3. Cross-version reference lookup
When requirements reference previous version APIs/auth logic:
1. `search_files` for interface paths, feature names across version management dir
2. Read matching `升级说明文档.md` to confirm auth/params
3. Reference accurately in current doc

### 4. Handle iteration (粗需求 → 详细需求)
1. First pass: write doc from rough requirements
2. User supplements: update with interface paths, auth details, field formats
3. Preserve original requirement descriptions

### 5. Screenshot management
- Name: `image-{keyword}.png` for team collaboration
- Relative path references: `![desc](./image-keyword.png)`
- When screenshot not yet provided: add `【截图参考】` section with placeholder list

### 6. Add SQL upgrade scripts
Place under `升级SQL/` subdir, numbered by execution order.

### 7. SVN commit
```bash
cd /mnt/d/项目/svn/P2040直采与框架协议/版本管理
svn add "{module}/{new_version}/"
svn commit -m "{version} {description}"
```

## Version Rollup
Structure for annual/quarterly rollups:
```markdown
## 版本升级统计
| 版本号 | 升级内容 | 升级时间 |
|--------|---------|---------|
| {version} | {content} | {date} |
```
Organize by category:
- 核心功能优化与新增
- 业务功能增强
- 平台适配与集成
- 系统性能与稳定性
- BUG修复

## Auth Patterns (common references)
See `references/auth-patterns.md` under this skill for common auth patterns used in upgrade docs.
