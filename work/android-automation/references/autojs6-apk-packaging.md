# AutoJs6 脚本打包独立 APK (实测流程 + 关键修复)

实测环境: WSL2 (无 sudo), Node v26, 便携 JDK 17。产物 `福袋助手.apk` 68MB, 签名 v2/v3 验证通过。

## 工具链
- 打包: [Steven-Qiang/AutoJs6-ApkBuilder](https://github.com/Steven-Qiang/AutoJs6-ApkBuilder) (npm `autojs6-apkbuilder` v1.1.0; 或 Java CLI `apkbuilder-cli.jar`)
- 签名: [patrickfav/uber-apk-signer](https://github.com/patrickfav/uber-apk-signer) v1.3.0 (V1+V2+V3, 单 jar)
- 模板: [SuperMonster003/AutoJs6](https://github.com/SuperMonster003/AutoJs6) releases 的 **arm64-v8a** APK (v6.7.0 ≈ 139MB; 另有 x86_64/universal 等变体)
- Java 17: WSL 无 sudo 时下载便携版 (Adoptium API, 解压即用):
  `curl -sL -o jdk.tar.gz "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse"`

## 打包命令
```bash
npm install autojs6-apkbuilder
curl -sL -o uber-apk-signer.jar \
  https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar

# ⚠️ 系统无 Java 时必须 export JAVA_HOME, 否则 find-java-home 报 ERR_INVALID_ARG_TYPE
export JAVA_HOME=$PWD/jdk/jdk-17.0.20+8
node node_modules/autojs6-apkbuilder/cli.js -a autojs6.apk -s ./autojs -o .build_raw.apk

# → 补回丢失资产 (见下节, 用 scripts/fix_apk_missing_assets.py)

keytool -genkeypair -keystore fudai.keystore -alias fudai -keyalg RSA -keysize 2048 \
  -validity 3650 -storepass PASS -keypass PASS -dname "CN=Fudai Helper, O=Personal, C=CN"
java -jar uber-apk-signer.jar -a .build_full.apk --ks fudai.keystore --ksAlias fudai \
  --ksPass PASS --ksKeyPass PASS --overwrite
mv .build_full.apk 福袋助手.apk
```

## ⚠️ autojs6-apkbuilder v1.1.0 的 bug (实测发现, 必须修复)
工具产物会丢失三类文件 (模板有, 产物无):
- `lib/<abi>/` — native 库 (模板 13 个 so, 含 `libRapidOcr.so`、`libmlkit_google_ocr_pipeline.so`)
- `assets/models/` — PaddleOCR onnx 模型 (`ch_PP-OCRv3_det/rec_infer.onnx` + cls + `ppocr_keys_v1.txt`)
- `assets/mlkit-google-ocr-models/` — MLKit 捆绑模型 (25 个)

不修复 → APK 装上即崩 (缺 native 库) / OCR 完全不可用 (缺模型)。
另外注意: 打包版**移除了插件系统** → 高精度 PP-OCRv5 插件装不上, 只能用内置 Paddle Lite 模型。
工具同时会合理裁剪: 去掉 docs/sample/editor/template.apk 等非运行时资源 (保留 fonts/web/modules/init.js)。

修复方式: 从模板把上述前缀的文件合并进产物 (已固化为 `scripts/fix_apk_missing_assets.py`), 然后**必须重新签名** (改 zip 内容使旧签名失效)。

## GitHub Actions 变体 (免本地环境)
ubuntu-latest 自带 java/keytool。workflow 内步骤:
1. `gh release download -R SuperMonster003/AutoJs6 -p 'autojs6-*-arm64-v8a-*.apk' -D . --clobber`
2. `npm install -g autojs6-apkbuilder` + 打包
3. python 内联补文件 (YAML 里 heredoc 注意公共缩进会被剥离, 相对缩进保留)
4. 下载 uber-apk-signer.jar → keytool 生成临时 keystore → 签名
5. `actions/upload-artifact@v4` 上传
完整 yaml 见用户项目 `autojs/.github/workflows/build-apk.yml` (已内置修复)。

## 签名与密钥
- uber-apk-signer 输出须含 `signature verified [v2, v3]` (现代 Android 必需 V2+)
- **keystore 必须随交付保留**: 以后升级 APK 必须用同一密钥签名, 否则无法覆盖安装 (只能卸载重装, 丢数据)
- 一键重打包: 固化整个流程为 `build_apk.sh` (检查模板/JDK/jar → 打包 → python 补文件 → keytool 建钥 → 签名 → 输出), 用户改脚本后一条命令重建

## 验证清单 (交付前)
1. `zipfile` 检查: `lib/` 存在且数量=模板; `assets/models/` 5 个; `assets/mlkit-google-ocr-models/` 25 个; `assets/project/<main>.js` **无明文** (AES 加密, 文件头 `77 01 17 7f...`)
2. 签名输出含 `signature verified [v2, v3]`
3. 体积参考: 模板 139MB → 修复后产物 ~69MB
4. 手机 arm64 (99% 现代机型); x86 模拟器需 x86_64 模板
