# LiteDock V1.1

Windows 10 轻量级桌面 Dock 原型，使用 Python + PySide6 构建。

## V1.1 更新

- 时钟显示秒数，格式为 `HH:MM:SS`，并显示日期。
- 增加电池电量和充/放电功率显示。Windows 通过 `Win32_Battery` 查询；若驱动不提供功率值，会显示“功率：不可读取”。台式机没有电池时会显示不可用。
- Dock 空白处右键菜单新增“关闭 LiteDock”与“设置”。
- 系统托盘菜单也有“关闭 LiteDock”。
- 设置里可开关电池信息显示。
- 仍默认不开机启动。

## 功能

- 无边框、置顶、半透明圆角 Dock
- 点击启动应用，右键编辑/移除
- 添加应用、拖放文件添加快捷入口
- 图标大小、背景不透明度、时钟和电池显示设置
- 系统托盘菜单
- 配置保存到 `%APPDATA%\\LiteDock\\config.json`

## 环境要求

- Windows 10 64 位
- Python 3.10–3.12（推荐 3.11）

## 运行源码

```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py main.py
```

## 本地构建 EXE

双击 `build.bat`，或运行：

```powershell
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --clean --windowed --onefile --name LiteDock main.py
```

生成文件：`dist\\LiteDock.exe`

## 使用 GitHub Actions 构建

1. 在 GitHub 创建仓库。
2. 上传本项目所有文件，保留 `.github/workflows/build.yml` 路径。
3. 打开仓库的 **Actions** 标签页并启用 Actions。
4. 推送代码，或手动运行 `Build LiteDock` 工作流。
5. 成功后，在运行记录的 Artifacts 下载 `LiteDock-Windows-x64`。

## 注意事项

这是轻量级第一阶段原型，不是系统级任务栏替代品。当前半透明背景不是完整 Windows Acrylic/Mica 模糊效果；图标悬停放大、窗口缩略图、自动隐藏、多屏细节仍可在后续版本实现。电池功率显示依赖电脑硬件和驱动提供 WMI 数据，部分机器只会显示电量或“功率：不可读取”。
