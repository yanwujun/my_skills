# 导购目录同步到集采市场 - 参考

## 场景

将某个源市场的导购目录（及所有子目录）同步到所有"集中采购"类型市场。

## 核心逻辑

1. WITH RECURSIVE 找出源市场指定根目录下的整棵子树
2. 与所有目标集采市场做 CROSS JOIN，每个市场生成一套副本
3. 修复新插入行的 UpStockDirId（仍指向源市场Id → 改为新Id）
4. 修复根节点的父指针指向目标市场同名路径的节点

## 关键变量

| 变量 | 说明 |
|------|------|
| @rootDirId | 源市场中要同步的目录根节点 Id |
| @marketId | 源市场 Id（TB_Market） |
| @maxDirId | 当前表最大Id，用于自增 |

## 注意事项

- 执行顺序不可变：INSERT → 修复自身UpId → 修复根父指针
- 不同步骤使用相同的CTE定义确保行号一致
- 建议先改 @rootDirId 为小范围测试，确认行数正确再全量执行
- 在 test 库备份：CREATE TABLE test.TB_B_ShopGuideDir_bak LIKE trade.TB_B_ShopGuideDir; INSERT ... SELECT ...
