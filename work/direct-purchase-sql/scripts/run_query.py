#!/usr/bin/env python3
"""
直采商城/框架协议 SQL 快捷查询工具。

在 WSL 终端直接运行 SQL 查询，避免手写 Python 连接模板。

用法：
  python3 run_query.py "SELECT COUNT(*) FROM TG_Goods WHERE State=1"
  python3 run_query.py xcj_mall_base "SELECT id, goodsName FROM TG_Goods LIMIT 5"
  python3 run_query.py ezc "SELECT projectName, projectNo FROM project ORDER BY id DESC LIMIT 10"
  python3 run_query.py trade "SELECT State, COUNT(*) FROM TF_Orders GROUP BY State"

默认库为 xcj_mall_base，可切换库（ezc / trade / stddata）。
输出格式：表格模式。
"""

import sys
import pymysql
from pymysql.cursors import DictCursor

HOST = '192.168.2.37'
PORT = 31004
USER = 'root'
PASSWORD = 'mysql'
DEFAULT_DB = 'xcj_mall_base'

def fmt_value(v):
    if v is None:
        return 'NULL'
    return str(v)

def main():
    args = sys.argv[1:]
    if not args:
        print('用法: python3 run_query.py [库名] "SQL语句"')
        print('       python3 run_query.py "SQL语句"  (默认库 xcj_mall_base)')
        sys.exit(1)

    if len(args) == 2:
        db = args[0]
        sql = args[1]
    else:
        db = DEFAULT_DB
        sql = args[0]

    conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD,
                           database=db, charset='utf8mb4', cursorclass=DictCursor)
    cur = conn.cursor()

    try:
        start = __import__('time').time()
        cur.execute(sql)
        elapsed = __import__('time').time() - start

        affected = cur.rowcount
        print(f'-- 数据库: {db}  |  影响行数: {affected}  |  耗时: {elapsed:.2f}s')
        print()

        # 如果是 SELECT 查询，打印结果
        if sql.strip().upper().startswith('SELECT') or sql.strip().upper().startswith('WITH'):
            rows = cur.fetchall()
            if not rows:
                print('(空结果集)')
            else:
                cols = list(rows[0].keys())
                # 列宽
                widths = {}
                for c in cols:
                    max_val = len(c)
                    for r in rows:
                        val_len = len(fmt_value(r[c]))
                        if val_len > max_val:
                            max_val = val_len
                    widths[c] = min(max_val + 2, 80)

                # 表头
                header = ' | '.join(c.ljust(widths[c]) for c in cols)
                sep = '-+-'.join('-' * widths[c] for c in cols)
                print(header)
                print(sep)

                # 数据行
                for r in rows:
                    line = ' | '.join(fmt_value(r[c]).ljust(widths[c]) for c in cols)
                    print(line)

                print(f'\n-- 共 {len(rows)} 行')

        elif sql.strip().upper().startswith('UPDATE') or sql.strip().upper().startswith('DELETE'):
            print('-- DML 已执行，请确认影响范围正确')
            print('-- 如需回滚，请从 test 库备份表恢复')

    except Exception as e:
        print(f'SQL 执行错误: {e}')
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
