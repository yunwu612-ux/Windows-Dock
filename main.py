import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QMenu, QSystemTrayIcon, QStyle, QMessageBox, QFrame,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QSlider, QSpinBox
)

APP_NAME = "LiteDock"
APP_VERSION = "1.1"
APP_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
CONFIG_PATH = APP_DIR / "config.json"


def default_config():
    return {
        "items": [
            {"name": "文件资源管理器", "path": "explorer.exe", "kind": "system", "icon": "folder"},
            {"name": "记事本", "path": "notepad.exe", "kind": "system", "icon": "text"},
        ],
        "dock_width": 540,
        "icon_size": 48,
        "opacity": 88,
        "position": "bottom",
        "show_clock": True,
        "show_battery": True,
    }


def load_config():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        defaults = default_config()
        for key, value in defaults.items():
            cfg.setdefault(key, value)
        cfg.setdefault("items", defaults["items"])
        return cfg
    except Exception:
        return default_config()


def save_config(cfg):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def make_icon(kind, size=64):
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    palette = {
        "folder": QColor("#f3c64e"),
        "text": QColor("#e9eef5"),
        "app": QColor("#78b7ff"),
    }
    color = palette.get(kind, palette["app"])
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    if kind == "folder":
        p.drawRoundedRect(7, 16, size-14, size-25, 8, 8)
        p.drawRoundedRect(10, 10, size//2, 15, 5, 5)
    elif kind == "text":
        p.drawRoundedRect(12, 5, size-24, size-10, 6, 6)
        p.setBrush(QColor("#7b8796"))
        for y in (20, 30, 40, 50):
            if y < size - 4:
                p.drawRoundedRect(19, y, size-38, 3, 1, 1)
    else:
        p.drawRoundedRect(6, 6, size-12, size-12, 14, 14)
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI", max(12, size//3), QFont.Weight.Bold))
        p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "L")
    p.end()
    return QIcon(pix)


class AddAppDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加应用")
        self.setMinimumWidth(420)
        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择 .exe、快捷方式或文件")
        browse = QPushButton("浏览…")
        browse.clicked.connect(self.browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse)
        layout.addRow("显示名称：", self.name_edit)
        layout.addRow("应用路径：", path_row)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择应用或快捷方式", str(Path.home()),
            "应用与快捷方式 (*.exe *.lnk *.bat *.cmd);;所有文件 (*.*)"
        )
        if path:
            self.path_edit.setText(path)
            if not self.name_edit.text().strip():
                self.name_edit.setText(Path(path).stem)

    def values(self):
        return self.name_edit.text().strip(), self.path_edit.text().strip()


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LiteDock 设置")
        self.config = config
        layout = QFormLayout(self)
        self.icon_size = QSpinBox()
        self.icon_size.setRange(32, 72)
        self.icon_size.setValue(int(config.get("icon_size", 48)))
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(55, 100)
        self.opacity.setValue(int(config.get("opacity", 88)))
        self.clock = QPushButton("显示" if config.get("show_clock", True) else "隐藏")
        self.clock.setCheckable(True)
        self.clock.setChecked(bool(config.get("show_clock", True)))
        self.clock.clicked.connect(lambda checked: self.clock.setText("显示" if checked else "隐藏"))
        self.battery = QPushButton("显示" if config.get("show_battery", True) else "隐藏")
        self.battery.setCheckable(True)
        self.battery.setChecked(bool(config.get("show_battery", True)))
        self.battery.clicked.connect(lambda checked: self.battery.setText("显示" if checked else "隐藏"))
        layout.addRow("图标大小：", self.icon_size)
        layout.addRow("背景不透明度：", self.opacity)
        layout.addRow("时钟：", self.clock)
        layout.addRow("电池信息：", self.battery)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def apply(self):
        self.config["icon_size"] = self.icon_size.value()
        self.config["opacity"] = self.opacity.value()
        self.config["show_clock"] = self.clock.isChecked()
        self.config["show_battery"] = self.battery.isChecked()


class DockWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.buttons = []
        self.drag_start = None
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAcceptDrops(True)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(8, 8, 8, 8)
        self.panel = QFrame()
        self.panel.setObjectName("panel")
        self.panel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.panel.customContextMenuRequested.connect(self.show_dock_context_menu)
        self.row = QHBoxLayout(self.panel)
        self.row.setContentsMargins(12, 9, 12, 9)
        self.row.setSpacing(8)
        self.root.addWidget(self.panel)

        self.setStyleSheet(self.style_for_opacity())
        self.rebuild()
        self.tray = self.make_tray()
        self.position_window()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(250)
        self.battery_timer = QTimer(self)
        self.battery_timer.timeout.connect(self.update_battery)
        self.battery_timer.start(30000)
        QTimer.singleShot(500, self.update_battery)

    def style_for_opacity(self):
        alpha = round(int(self.config.get("opacity", 88)) * 2.55)
        return f"""
        QFrame#panel {{
            background-color: rgba(27, 31, 39, {alpha});
            border: 1px solid rgba(255, 255, 255, 42);
            border-radius: 20px;
        }}
        QPushButton {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: 12px;
            padding: 3px;
            color: #f4f7fb;
            font-size: 11px;
        }}
        QPushButton:hover {{
            background-color: rgba(255,255,255,34);
            border: 1px solid rgba(255,255,255,48);
        }}
        QLabel {{ color: #f4f7fb; }}
        """

    def make_tray(self):
        tray = QSystemTrayIcon(make_icon("app", 32), self)
        menu = QMenu()
        show_action = QAction("显示 Dock", self)
        show_action.triggered.connect(self.show)
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        close_action = QAction("关闭 LiteDock", self)
        close_action.triggered.connect(QApplication.quit)
        menu.addAction(show_action)
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(close_action)
        tray.setContextMenu(menu)
        tray.setToolTip(f"LiteDock {APP_VERSION}")
        tray.show()
        return tray

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def rebuild(self):
        self.clear_layout(self.row)
        self.buttons = []
        icon_size = int(self.config.get("icon_size", 48))
        for idx, item in enumerate(self.config.get("items", [])):
            btn = QPushButton()
            btn.setToolTip(f"{item.get('name', '应用')}\n{item.get('path', '')}")
            btn.setIcon(self.icon_for_item(item))
            btn.setIconSize(QSize(icon_size, icon_size))
            btn.setFixedSize(icon_size + 12, icon_size + 14)
            btn.clicked.connect(lambda checked=False, i=idx: self.launch_item(i))
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, i=idx, b=btn: self.item_menu(i, b.mapToGlobal(pos)))
            self.row.addWidget(btn)
            self.buttons.append(btn)

        add_btn = QPushButton("+")
        add_btn.setToolTip("添加应用")
        add_btn.setFixedSize(36, icon_size + 14)
        add_btn.setStyleSheet("font-size: 26px; font-weight: 300;")
        add_btn.clicked.connect(self.add_app)
        self.row.addWidget(add_btn)

        settings_btn = QPushButton("⚙")
        settings_btn.setToolTip("设置")
        settings_btn.setFixedSize(34, icon_size + 14)
        settings_btn.clicked.connect(self.open_settings)
        self.row.addWidget(settings_btn)

        self.clock_label = None
        self.battery_label = None
        if self.config.get("show_battery", True):
            self.battery_label = QLabel("电池信息读取中…")
            self.battery_label.setMinimumWidth(115)
            self.battery_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.battery_label.setStyleSheet("font-size: 11px;")
            self.battery_label.setToolTip("Windows 电池状态与充放电功率（设备支持时显示）")
            self.row.addWidget(self.battery_label)

        if self.config.get("show_clock", True):
            self.clock_label = QLabel()
            self.clock_label.setMinimumWidth(88)
            self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.clock_label.setStyleSheet("font-size: 12px;")
            self.row.addWidget(self.clock_label)
            self.update_clock()
        self.setStyleSheet(self.style_for_opacity())
        self.adjustSize()
        self.position_window()
        self.update_battery()

    def icon_for_item(self, item):
        path = item.get("path", "")
        if item.get("kind") == "system":
            return make_icon(item.get("icon", "app"), 64)
        if path and os.path.exists(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon
        return self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

    def update_clock(self):
        if self.clock_label is not None:
            self.clock_label.setText(datetime.now().strftime("%H:%M:%S\n%Y/%m/%d"))

    def update_battery(self):
        if self.battery_label is None:
            return
        # Prefer Windows WMI values for battery charge and charge/discharge rate.
        # Some laptops/drivers do not expose EstimatedChargeRate; in that case show a clear fallback.
        ps_script = (
            "$b=Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1 "
            "EstimatedChargeRemaining,BatteryStatus,EstimatedChargeRate; "
            "if($null -eq $b){'NO_BATTERY'}else{"
            "$b | ConvertTo-Json -Compress}"
        )
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True, text=True, timeout=4,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            raw = result.stdout.strip()
            if not raw or raw == "NO_BATTERY":
                self.battery_label.setText("电池：不可用")
                self.battery_label.setToolTip("此电脑未检测到可读取的电池信息")
                return
            data = json.loads(raw)
            percent = data.get("EstimatedChargeRemaining")
            status = int(data.get("BatteryStatus") or 0)
            rate = data.get("EstimatedChargeRate")
            status_text = {
                1: "放电中", 2: "接通电源", 3: "已充满", 4: "电量低",
                5: "电量严重不足", 6: "充电中", 7: "充电中", 8: "充电中",
                9: "充电中", 10: "状态未知", 11: "部分充电"
            }.get(status, "状态未知")
            direction = "输入" if status in (2, 6, 7, 8, 9, 11) else "输出"
            if rate is None or str(rate).strip() == "":
                power_text = "功率：不可读取"
            else:
                watts = abs(float(rate)) / 1000.0
                power_text = f"{direction} {watts:.1f} W"
            percent_text = f"{int(percent)}%" if percent is not None else "--%"
            self.battery_label.setText(f"电池 {percent_text}\n{power_text}")
            self.battery_label.setToolTip(
                f"电池电量：{percent_text}\n状态：{status_text}\n"
                f"充放电功率：{power_text}\n"
                "功率读数取决于 Windows 电池驱动是否提供数据。"
            )
        except subprocess.TimeoutExpired:
            self.battery_label.setText("电池：读取超时")
        except Exception:
            self.battery_label.setText("电池：不可读取")
            self.battery_label.setToolTip(
                "无法读取电池信息。桌面电脑可能没有电池，或设备驱动未提供 WMI 数据。"
            )

    def position_window(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        self.adjustSize()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + geo.height() - self.height() - 22
        self.move(x, y)

    def launch_item(self, index):
        try:
            item = self.config["items"][index]
            path = item["path"]
            if not path:
                return
            if os.path.isabs(path) and not os.path.exists(path):
                QMessageBox.warning(self, "找不到应用", f"路径不存在：\n{path}")
                return
            if path.lower().endswith((".lnk", ".url")):
                os.startfile(path)
            elif os.path.isabs(path):
                os.startfile(path)
            else:
                subprocess.Popen(path, shell=True)
        except Exception as exc:
            QMessageBox.warning(self, "启动失败", str(exc))

    def item_menu(self, index, global_pos):
        menu = QMenu(self)
        launch = menu.addAction("启动")
        rename = menu.addAction("编辑名称/路径")
        remove = menu.addAction("从 Dock 移除")
        chosen = menu.exec(global_pos)
        if chosen == launch:
            self.launch_item(index)
        elif chosen == remove:
            self.config["items"].pop(index)
            save_config(self.config)
            self.rebuild()
        elif chosen == rename:
            item = self.config["items"][index]
            dialog = AddAppDialog(self)
            dialog.setWindowTitle("编辑应用")
            dialog.name_edit.setText(item.get("name", ""))
            dialog.path_edit.setText(item.get("path", ""))
            if dialog.exec() == QDialog.DialogCode.Accepted:
                name, path = dialog.values()
                if name and path:
                    item["name"], item["path"] = name, path
                    item["kind"] = "custom"
                    save_config(self.config)
                    self.rebuild()

    def show_dock_context_menu(self, pos):
        menu = QMenu(self)
        settings_action = menu.addAction("设置")
        close_action = menu.addAction("关闭 LiteDock")
        chosen = menu.exec(self.panel.mapToGlobal(pos))
        if chosen == settings_action:
            self.open_settings()
        elif chosen == close_action:
            QApplication.quit()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        settings_action = menu.addAction("设置")
        close_action = menu.addAction("关闭 LiteDock")
        chosen = menu.exec(event.globalPos())
        if chosen == settings_action:
            self.open_settings()
        elif chosen == close_action:
            QApplication.quit()

    def add_app(self):
        dialog = AddAppDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, path = dialog.values()
            if not name:
                name = Path(path).stem if path else "新应用"
            if path:
                self.config["items"].append({"name": name, "path": path, "kind": "custom"})
                save_config(self.config)
                self.rebuild()

    def open_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dialog.apply()
            save_config(self.config)
            self.rebuild()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        changed = False
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and os.path.isfile(path):
                self.config["items"].append({
                    "name": Path(path).stem,
                    "path": path,
                    "kind": "custom",
                })
                changed = True
        if changed:
            save_config(self.config)
            self.rebuild()
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_start and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_start
            self.move(self.pos() + delta)
            self.drag_start = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_start = None
        super().mouseReleaseEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    window = DockWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
