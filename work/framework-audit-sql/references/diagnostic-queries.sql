-- ============================================================
-- 诊断：AI审核查询无数据的排查步骤
-- 数据库：show1-zcj (192.168.2.37:31404)
-- ============================================================

-- ① ai_audit_session 表是否有数据？
SELECT COUNT(*) FROM ezc.ai_audit_session;

-- ② 指定时间段内有多少条会话？
SELECT COUNT(*) FROM ezc.ai_audit_session
WHERE createTime >= 'YYYY-MM-DD HH:MM:SS'
  AND createTime <= 'YYYY-MM-DD HH:MM:SS';

-- ③ oper_record 中 AI审核记录总数？
SELECT COUNT(*) FROM ezc.oper_record
WHERE businessCode IN ('GOODS_COMPLETE_AUDIT', 'GOODS_MODIFY_AUDIT')
  AND operName IN ('智能审核通过', '智能审核退回');

-- ④ oper_record 中人工审核记录总数？
SELECT COUNT(*) FROM ezc.oper_record
WHERE businessCode IN ('GOODS_COMPLETE_AUDIT', 'GOODS_MODIFY_AUDIT')
  AND operName IN ('初审通过', '通过', '退回');

-- ⑤ oper_record 操作类型分布
SELECT operName, operType, COUNT(*) AS cnt
FROM ezc.oper_record
WHERE businessCode IN ('GOODS_COMPLETE_AUDIT', 'GOODS_MODIFY_AUDIT')
GROUP BY operName, operType
ORDER BY cnt DESC;

-- ⑥ oper_record 时间范围
SELECT MIN(operTime), MAX(operTime) FROM ezc.oper_record;

-- ⑦ 查看一条 resultJson 样例
SELECT id, LEFT(resultJson, 500) FROM ezc.ai_audit_session
WHERE resultJson IS NOT NULL AND status = 'COMPLETED'
LIMIT 1;
