# LiteDock

一个面向 Windows 10 的轻量级桌面 Dock 原型，使用 Python + PySide6 构建。它借鉴了常见桌面 Dock 的交互方式，不是 MyDockFinder 的复制品。

## 当前功能

- 无边框、置顶、半透明圆角 Dock
- 应用图标按钮，点击启动应用
- 添加应用、右键编辑/移除
- 拖放文件到 Dock 添加快捷入口
- 图标大小、背景不透明度、时钟显示设置
- 系统托盘菜单
- 配置保存在 `%APPDATA%\\LiteDock\\config.json`
- 默认不开机启动

## 环境要求

- Windows 10 64 位
- Python 3.10–3.12（推荐 3.11）
- 网络连接，用于安装依赖

## 运行源码

```powershell
py -m venv .venv
.venv\\Scripts\\activate
py -m pip install -r requirements.txt
py main.py
```

如果 `py` 命令不可用，请安装 Python，并在安装时勾选 **Add Python to PATH**。

## 构建 EXE

双击 `build.bat`，或在 PowerShell 中执行：

```powershell
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --clean --windowed --onefile --name LiteDock main.py
```

生成文件：`dist\\LiteDock.exe`

首次启动可能被 Windows 安全提示检查；请只运行自己构建或可信来源的文件。打包后的单文件程序启动可能比目录版慢一点。若更重视启动速度，可把 `--onefile` 改为 `--onedir`。

## 使用方法

- 点击 `+` 添加 `.exe`、`.lnk` 或其他可打开文件。
- 右键应用图标可以启动、编辑或移除。
- 将文件拖到 Dock 上可添加快捷入口。
- 点击齿轮图标调整图标大小、透明度和时钟。
- 右键系统托盘图标可以显示 Dock、打开设置或退出。

## GitHub Actions 构建

1. 在 GitHub 新建一个空仓库，例如 `LiteDock`。
2. 上传本项目全部文件（包括 `.github/workflows/build.yml`）。
3. 打开仓库的 **Actions** 标签页，启用 Actions。
4. 推送代码或手动运行 `Build LiteDock` 工作流。
5. 在工作流运行结果的 **Artifacts** 区域下载 `LiteDock-Windows-x64`，里面包含 EXE。

GitHub Actions 构建流程见 `.github/workflows/build.yml`。

## 已知限制 / 后续计划

这是第一版原型：目前不是系统级任务栏替代品，图标悬停放大动画、窗口缩略图、自动隐藏、显示器选择、DPI/多屏细节和原生 Windows Acrylic/Mica 效果尚未实现。当前透明背景使用 Qt 半透明绘制，并非完整系统毛玻璃模糊。可在后续版本逐步补齐。
