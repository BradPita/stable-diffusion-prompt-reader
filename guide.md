# SD Prompt Reader 打包与发布技术指引

本文件记录了使用 GitHub Actions + PyInstaller 打包此项目（包含 CustomTkinter 和 TkinterDnD2）时的核心配置说明与常见报错排查指南。

## 1. 核心打包参数说明

在 `.github/workflows/` 下的 `.yml` 文件中，我们使用 `pyinstaller` 命令进行打包。以下是关键参数的详细解释：

### 1.1 基础参数
* `--noconfirm`：覆盖之前生成的 `dist` 和 `build` 文件夹，无需手动确认。
* `--windowed` (或 `-w`)：隐藏终端控制台。对于 GUI 程序是必须的，否则双击运行时会弹出一个黑色的命令行窗口。注意：Mac 上使用此参数会生成 `.app` 文件夹。
* `--onefile` (或 `-F`)：将所有依赖打包成单个可执行文件（仅 Windows 使用）。Mac 不建议使用，因为 Mac 的 `.app` 本质是文件夹，使用单文件模式可能导致某些资源路径解析异常且启动较慢。
* `--name "SD Prompt Reader"`：指定输出的程序名称。

### 1.2 资源文件打包 (`--add-data`)
PyInstaller 默认**只打包 `.py` 文件**，不会打包 `.json`、`.png` 等静态资源。必须手动指定。

* **语法**：`--add-data "源路径:目标路径"` (Mac/Linux) 或 `--add-data "源路径;目标路径"` (Windows)
* **项目实例**：CustomTkinter 需要读取主题文件 `gray.json`，如果不加此参数会报 `FileNotFoundError`。
  * Mac: `--add-data "sd_prompt_reader/resources:sd_prompt_reader/resources"`
  * Win: `--add-data "sd_prompt_reader/resources;sd_prompt_reader/resources"`

### 1.3 复杂库全量打包 (`--collect-all`)
某些第三方库（如拖拽库 `tkinterdnd2` 和 UI库 `customtkinter`）底层包含 C 语言编译的动态链接库（`.dll`/`.dylib`）或 Tcl/Tk 脚本。PyInstaller 的静态分析无法识别它们，必须使用 `--collect-all` 强制将指定库的所有关联文件打包进去。

* **项目实例**：
  * `--collect-all tkinterdnd2`：解决 `RuntimeError: Unable to load tkdnd library` 报错。
  * `--collect-all customtkinter`：解决 UI 组件渲染异常或主题找不到的问题。

---

## 2. 完整的 GitHub Actions 配置参考

以下是当前可用的、跨平台（Windows + macOS）的完整打包配置：

```yaml
name: Auto Build Executables

on:
  push:
    branches: [ "SimpAI" ]
  workflow_dispatch:

jobs:
  build:
    name: Build on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest]

    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller

    - name: Build with PyInstaller (Windows)
      if: matrix.os == 'windows-latest'
      run: pyinstaller --onefile --windowed --noconfirm --name "SD Prompt Reader" --add-data "sd_prompt_reader/resources;sd_prompt_reader/resources" --collect-all tkinterdnd2 --collect-all customtkinter main.py

    - name: Build with PyInstaller (macOS)
      if: matrix.os == 'macos-latest'
      run: pyinstaller --windowed --noconfirm --name "SD Prompt Reader" --add-data "sd_prompt_reader/resources:sd_prompt_reader/resources" --collect-all tkinterdnd2 --collect-all customtkinter main.py

    - name: Zip macOS App
      if: matrix.os == 'macos-latest'
      run: |
        cd dist
        zip -r "SD-Prompt-Reader-macOS.zip" "SD Prompt Reader.app"

    - name: Upload Artifact (Windows)
      if: matrix.os == 'windows-latest'
      uses: actions/upload-artifact@v4
      with:
        name: SD-Prompt-Reader-Windows
        path: "dist/SD Prompt Reader.exe"

    - name: Upload Artifact (macOS)
      if: matrix.os == 'macos-latest'
      uses: actions/upload-artifact@v4
      with:
        name: SD-Prompt-Reader-macOS
        path: "dist/SD-Prompt-Reader-macOS.zip"
```

---

## 3. 常见报错与排查指南 (FAQ)

### Q1: Mac 双击 `.app` 没反应，终端运行报 `Error: Missing option '-i'`？
**原因**：`main.py` 中的 `is_console()` 判断逻辑在双击运行时失效，导致程序误以为在命令行模式运行。
**解决**：在终端中使用 `< /dev/null` 模拟无输入环境运行以获取真实报错：`./SD\ Prompt\ Reader.app/Contents/MacOS/SD\ Prompt\ Reader < /dev/null`。或者直接在 `main.py` 中强制运行 `main()`。

### Q2: 报错 `FileNotFoundError: ... gray.json`？
**原因**：`customtkinter` 的主题文件未被打包。
**解决**：在打包命令中增加 `--add-data "sd_prompt_reader/resources:sd_prompt_reader/resources"` (注意 Mac 用 `:`，Win 用 `;`)。

### Q3: 报错 `RuntimeError: Unable to load tkdnd library`？
**原因**：`tkinterdnd2` 拖拽库的底层 C 动态链接库未被打包。
**解决**：在打包命令中增加 `--collect-all tkinterdnd2`。

### Q4: Mac 下载下来的 `.app` 双击还是没反应？
**原因**：macOS 的安全机制拦截了未签名的第三方 App。
**解决**：在终端执行命令解除隔离属性：`xattr -cr /路径/到/SD\ Prompt\ Reader.app`

---

## 4. 如何在本地测试打包（不依赖 GitHub Actions）

在将代码推送到 GitHub 之前，你可以在本地先测试打包是否成功。

1. 确保安装了 pyinstaller：`pip install pyinstaller`
2. 在项目根目录（`main.py` 所在目录）打开终端。
3. 运行以下命令（以 Mac 为例）：
   ```bash
   pyinstaller --windowed --noconfirm --name "SD Prompt Reader" --add-data "sd_prompt_reader/resources:sd_prompt_reader/resources" --collect-all tkinterdnd2 --collect-all customtkinter main.py
   ```
4. 打包完成后，会在项目下生成 `dist` 文件夹，里面就是打包好的程序。本地测试无误后再推送到 GitHub。
