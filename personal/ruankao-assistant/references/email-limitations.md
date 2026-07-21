# QQ邮箱环境限制

## 发送邮件 (SMTP) ✅ 可用

```python
import smtplib
from email.mime.text import MIMEText
from email.header import Header

msg = MIMEText(content, 'plain', 'utf-8')
msg['From'] = '1043769802@qq.com'
msg['To'] = '1043769802@qq.com'
msg['Subject'] = Header('标题', 'utf-8')

server = smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=30)
server.login('1043769802@qq.com', 'efrisbwuicqkbccj')
server.sendmail('1043769802@qq.com', ['1043769802@qq.com'], msg.as_string())
server.quit()
```

- SMTP Host: `smtp.qq.com`
- SSL Port: 465
- 授权码: `efrisbwuicqkbccj`

## 接收邮件 (IMAP) ❌ 不可用

从当前 WSL 环境 **无法连接** `imap.qq.com:993`，始终超时。

```python
# 这行不通 — 会永久卡住/超时
imaplib.IMAP4_SSL('imap.qq.com', 993)
```

这意味着：
- ❌ 不能通过命令行/Python 读取QQ邮箱收件箱
- ❌ 不能自动检测新邮件
- ❌ 不能搜索历史邮件

## 替代方案

- 用户自行在浏览器打开 https://mail.qq.com 查看收件箱
- 代理/转发：将QQ邮件转发到其他可用邮箱（如Gmail）
- 通过QQ消息本身接收通知（QQ邮箱App有消息推送）
