# Protocol-01: 零依赖手工构建 APK 流水线 (Raw APK Pipeline)

> **目标**：不依赖庞大的 Android Studio 或 Gradle，直接在手机 Linux 沙盒（Termux/PRoot）内利用基础构建工具（aapt2、javac、d8/dx、zipalign、apksigner）将源码手搓为标准 APK。

---

## 💣 常见 AI 踩坑实录 (Hallucinations & Failures)

1. **`resources.arsc` 压缩暴毙**：AI 打包时直接用 `zip -r app.apk .`，导致 `resources.arsc` 被 Deflate 压缩。在 Android 8.0+ 上安装直接报错：`INSTALL_FAILED_INVALID_APK: Failure [-124: Failed to extract native libraries, res files uncompressed and aligned]`.
2. **SELinux 隔离导致 pm 找不到安装包**：AI 在 Linux PRoot 私有目录生成了 `/root/app.apk`，然后让用户执行 `pm install /root/app.apk`。Android 母系统的 `pm` 根本没有权限读取 PRoot 的私有沙盒路径。
3. **缺少图标导致安装闪退或白图标**：AI 生成清单时忘记配置 `android:icon`，或者写了引向不存在的 PNG。
4. **Target SDK 版本坑**：未指定或设置过高，导致 Android 系统弹出权限阻断。

---

## 🛠️ 标准化避坑流程 (The Robust Pipeline)

### 步骤 1：编译资源 (aapt2 compile & link)
```bash
# 1. 编译 XML 资源与布局
aapt2 compile res/layout/activity_main.xml -o compiled/
aapt2 compile res/values/strings.xml -o compiled/

# 2. 链接并生成未压缩的 APK 原型与 R.java
aapt2 link -I /path/to/android.jar \
    --manifest AndroidManifest.xml \
    --java src/ \
    -o base.apk \
    compiled/*.flat
```

### 步骤 2：编译 Java 代码为 Dex (javac + d8)
```bash
# 1. 编译 Java 源码
javac -d obj/ -cp /path/to/android.jar src/com/example/app/*.java

# 2. 转换为 Android Dex 字节码
d8 --output . obj/com/example/app/*.class
```

### 步骤 3：打包与资源不压缩铁律 (Zip Handling) ⚠️
```bash
# 将 classes.dex 添加进 base.apk
zip -u base.apk classes.dex

# 【致命关键点】：resources.arsc 必须是 0 压缩存储！
# 如果 aapt2 默认压缩了，必须用 zip -0 强制无压缩覆盖：
zip -0 -u base.apk resources.arsc
```

### 步骤 4：对齐与签名 (zipalign & apksigner)
```bash
# 4 字节边界对齐
zipalign -v -p 4 base.apk aligned.apk

# 使用 v1 + v2 签名
apksigner sign --ks release.keystore --ks-pass pass:android --out app-signed.apk aligned.apk
```

### 步骤 5：跨沙盒安全安装 (SELinux Bypass) ⚠️
在终端与安卓系统母体之间安装应用，必须经过中转公共缓冲目录：
```bash
# 1. 将签名好的 APK 拷贝到中转目录
cp app-signed.apk /data/local/tmp/app.apk
# 或拷贝到公有存储
cp app-signed.apk /sdcard/Download/app.apk

# 2. 调用安卓母系统 pm 命令安装
pm install -r /data/local/tmp/app.apk
```