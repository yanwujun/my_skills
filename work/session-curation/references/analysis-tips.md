# Session Analysis Tips

## 快速判断策略

### 快速识别"有无沉淀价值"的5个信号
1. 会话标题是否指向具体任务（"版本信息查询"→ 无，"生成GitLab SSH密钥"→ 可能有）
2. 用户是否提出了后续复用请求（"帮我建一个skill"→ 有）
3. 用户是否纠正了我（"以后不要XXX"→ 有）
4. 是否运行了独特的命令/脚本序列 → 可能有
5. 对话长度：<5条消息几乎无价值，>20条消息有较大可能

### 记忆合并的典型模式

| 新信息类型 | 应该合并到的目标记忆条目 |
|-----------|----------------------|
| 新仓库位置/新Git账号 | "note仓库 ~/note(gitee:...)" 条目 |
| 新工具安装路径/环境配置 | "Cursor配置在Windows ..." 条目 |
| 新数据库连接/表结构 | "已建两个SQL skill" 条目 |
| 用户偏好/沟通风格 | user profile（由session-curation cron读取，但记忆增加走memory target=user） |

### 效率技巧

- **session_search(browse) 只返回最近 3 个会话**，不是全量。必须追加一次 discover 搜索：`session_search(query="user OR assistant", limit=10, sort="newest")` 来覆盖历史会话。
- 对一个长会话（100+条），只看 bookend_start（开始目标）+ bookend_end（最终结果）+ 中间的消息中是否包含 memory/skill_manage/skill_view 工具调用（这些是已沉淀的标志）
- 对于 cron 任务的会话（source=cron），直接跳过
- 如果某个会话已经触发了 memory 或 skill_manage 工具调用，说明已有其他会话处理过这部分内容，小心不要重复沉淀

### Cron 模式下的替代工具链

cron job 运行时 `execute_code` 完全 blocked，`terminal` 的 Python `-c` 需审批（无用户=blocked）。用以下替代方案处理大 JSON 结果：

| 需求 | 替代命令 |
|------|---------|
| 提取所有 session_id | `grep -oP '"session_id":\s*"\K[^"]+' file \| sort -u` |
| 获取最后一条消息时间戳 | `grep -oP '"timestamp":\s*\K[\d.]+' file \| tail -1` |
| 读取大文件尾部 | `tail -c 3000 file`（3000 字节约覆盖 bookend 区域） |
| 查看 session_meta 信息 | `grep -oP '"session_meta":\s*\{[^}]+\}' file` |
| 提取最后几条消息角色 | `grep -oP '"role":\s*"[^"]*"\|"timestamp":\s*[\d.]+' file \| tail -30` |
