# WSL 下 HuggingFace 模型下载代理配置

## 问题

WSL 环境通常需要通过 Windows 主机的代理才能访问外网。直接 `pip install` 没问题，但 `diffusers.from_pretrained()` 下载 HuggingFace 模型时需要 HTTP 代理。

## 代理配置

在 Python 脚本中显式设置（不要依赖环境变量继承）：

```python
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:8888'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:8888'
os.environ['http_proxy'] = 'http://127.0.0.1:8888'
os.environ['https_proxy'] = 'http://127.0.0.1:8888'
```

## 已知问题

| 问题 | 现象 | 解决 |
|------|------|------|
| 使用 HF Mirror 时 401 | `hf-mirror.com` 对某些模型返回 401 | 切回 main endpoint，用代理走外网 |
| 代理超时 | 大文件下载（>1GB）可能被代理中断 | 使用小模型如 OFA-Sys/small-stable-diffusion-v0（335MB） |
| 模型需要认证 | FLUX.1-schnell 等 gated model 返回 401 | 使用公开模型，如 sd-legacy/stable-diffusion-v1-5 |
| `execute_code` 工具无 torch | execute_code 的 Python 环境没有 torch | 必须用 `terminal` 工具运行生成脚本 |

## 验证网络连通性

```bash
curl -sI https://huggingface.co/OFA-Sys/small-stable-diffusion-v0/resolve/main/model_index.json | head -3
```

如果返回 200 或 302，则代理正常。

## 模型推荐（按下载量排序，越小越快）

| 模型 | 大小 | 步骤 | 质量 | 备注 |
|------|------|------|------|------|
| OFA-Sys/small-stable-diffusion-v0 | 335MB | 50 steps | 中低 | 下载最快，适合有限环境 |
| sd-legacy/stable-diffusion-v1-5 | 1.9GB | 30 steps | 中 | SD1.5 标准版 |
| stabilityai/sd-turbo | 6.7GB | 1 step | 高 | 质量最好但下载慢 |
| stabilityai/stable-diffusion-2-1-base | ~2GB | 30 steps | 中高 | 需要 HF 认证 |
