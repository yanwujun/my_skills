#!/usr/bin/env python3
"""修复 autojs6-apkbuilder v1.1.0 打包产物丢失的资产 (native 库 + OCR 模型).

用法:
    python3 fix_apk_missing_assets.py <模板.apk> <工具产物.apk> <输出.apk>

从模板 APK 把 lib/、assets/models/、assets/mlkit-google-ocr-models/
补回工具产物, 生成新 APK。改 zip 内容后旧签名失效, 必须重新签名
(uber-apk-signer / apksigner)。
"""
import sys
import zipfile

EXTRA_PREFIXES = ('lib/', 'assets/models/', 'assets/mlkit-google-ocr-models/')


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    tpl_path, src_path, out_path = sys.argv[1:4]
    tpl = zipfile.ZipFile(tpl_path)
    src = zipfile.ZipFile(src_path)
    extras = [n for n in tpl.namelist() if n.startswith(EXTRA_PREFIXES)]
    total = sum(tpl.getinfo(n).file_size for n in extras)
    print(f"补入 {len(extras)} 个文件 ({total/1048576:.1f} MB): "
          f"lib/ {sum(n.startswith('lib/') for n in extras)} 个, "
          f"models/ {sum(n.startswith('assets/models/') for n in extras)} 个, "
          f"mlkit/ {sum(n.startswith('assets/mlkit-google-ocr-models/') for n in extras)} 个")
    out = zipfile.ZipFile(out_path, 'w')
    for n in src.namelist():
        if n.startswith(EXTRA_PREFIXES):
            continue
        out.writestr(src.getinfo(n), src.read(n))
    for n in extras:
        out.writestr(tpl.getinfo(n), tpl.read(n))
    out.close()
    print(f"完成: {out_path} (总文件 {len(zipfile.ZipFile(out_path).namelist())})")
    print("注意: 内容已变更, 旧签名失效, 请用 uber-apk-signer 重新签名!")


if __name__ == '__main__':
    main()
