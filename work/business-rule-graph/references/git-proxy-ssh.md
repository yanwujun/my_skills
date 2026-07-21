# WSL SSH 通过 HTTP 代理连接 GitHub

## 问题

WSL 环境下直连 GitHub 端口 22 超时（公司网络/防火墙阻断 TCP 直连），但 HTTP 代理（sing-box 等）可用。

## 修复

在 `~/.ssh/config` 中添加 ProxyCommand：

```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes
    ProxyCommand nc -X connect -x 127.0.0.1:8888 %h %p
```

`nc -X connect` 使用 HTTP CONNECT 隧道，让 SSH 流量套 HTTP 壳从代理出去。

## 验证

```bash
ssh -T git@github.com
# 预期: Hi <username>! You've successfully authenticated...
```
