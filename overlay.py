"""Transparent, always-on-top Windows host for the local particle scene."""

from __future__ import annotations

import argparse
import ctypes
import json
import sys
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QAbstractNativeEventFilter, Qt, QUrl, QUrlQuery
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView


ROOT = Path(__file__).resolve().parent


class Hotkeys(QAbstractNativeEventFilter):
    """Register keys with Windows so the editor can retain keyboard focus."""

    def __init__(self, window: Overlay):
        super().__init__()
        self.window = window
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        self.user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        self.registered = []
        self.actions = {1: window.restart, 2: window.burst, 3: window.toggle_visibility, 4: QApplication.quit}
        self.failed = []
        for ident, letter in [(1, 'R'), (2, 'B'), (3, 'H'), (4, 'Q')]:
            # MOD_CONTROL | MOD_ALT | MOD_SHIFT | MOD_NOREPEAT
            if self.user32.RegisterHotKey(int(window.winId()), ident, 0x4007, ord(letter)):
                self.registered.append(ident)
            else:
                self.failed.append(f'Ctrl+Alt+Shift+{letter}')

    def nativeEventFilter(self, event_type, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == 0x0312 and msg.wParam in self.actions:
            self.actions[msg.wParam]()
            return True, 0
        return False, 0

    def close(self):
        for ident in self.registered:
            self.user32.UnregisterHotKey(int(self.window.winId()), ident)
        self.registered.clear()


class LocalPage(QWebEnginePage):
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        # The desktop host only needs the bundled local scene.
        return url.isLocalFile() and Path(url.toLocalFile()).resolve() == ROOT / 'index.html'


class Overlay(QWebEngineView):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.setWindowTitle('星愿 · 桌面悬浮圣诞树')
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet('background: transparent;')
        self.setPage(LocalPage(self))
        self.page().setBackgroundColor(QColor(0, 0, 0, 0))
        self.loadFinished.connect(self.loaded)
        screens = QApplication.screens()
        if not 0 <= args.screen < len(screens):
            raise ValueError(f'屏幕编号应在 0 到 {len(screens) - 1} 之间')
        area = screens[args.screen].availableGeometry()
        height = min(args.height or int(area.height() * .94), area.height())
        width = min(args.width or int(height * .85), area.width())
        x = args.x if args.x is not None else area.right() - width - 12
        y = args.y if args.y is not None else area.y() + (area.height() - height) // 2
        self.setGeometry(x, y, width, height)
        url = QUrl.fromLocalFile(str(ROOT / 'index.html'))
        query = QUrlQuery()
        query.addQueryItem('overlay', '1')
        url.setQuery(query)
        self.load(url)

    def showEvent(self, event):
        super().showEvent(event)
        # Enforce NOACTIVATE on the native host as well as the Qt focus policy.
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
        user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
        handle = int(self.winId())
        styles = user32.GetWindowLongPtrW(handle, -20)
        # WS_EX_NOACTIVATE | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
        user32.SetWindowLongPtrW(handle, -20, styles | 0x08000000 | 0x20 | 0x80)

    def loaded(self, ok):
        if not ok:
            QMessageBox.critical(None, '星愿', '无法加载本地场景，请确保 index.html 与 overlay.py 在同一目录。')
            QApplication.quit()
            return
        self.page().runJavaScript(
            f'ice={str(self.args.theme == "ice").lower()};wish={json.dumps(self.args.wish, ensure_ascii=True)};'
        )

    def restart(self):
        self.page().runJavaScript('replay()')

    def burst(self):
        self.page().runJavaScript('burstAt=lastTime')

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())


def tray_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor('#f3d28c'))
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QPolygonF
    painter.drawPolygon(QPolygonF([QPointF(32, 3), QPointF(56, 49), QPointF(8, 49)]))
    painter.drawRect(28, 48, 8, 12)
    painter.end()
    return QIcon(pixmap)


def parse_args():
    parser = argparse.ArgumentParser(description='透明置顶、鼠标穿透的桌面粒子圣诞树（Windows）')
    parser.add_argument('--screen', type=int, default=0, help='屏幕编号，从 0 开始')
    parser.add_argument('--width', type=int, help='悬浮区域宽度，逻辑像素')
    parser.add_argument('--height', type=int, help='悬浮区域高度，逻辑像素')
    parser.add_argument('--x', type=int, help='区域左上角的桌面 X 坐标')
    parser.add_argument('--y', type=int, help='区域左上角的桌面 Y 坐标')
    parser.add_argument('--theme', choices=['gold', 'ice'], default='gold')
    parser.add_argument('--wish', default='愿所有美好，如期而至', help='自定义祝福，最多 24 字')
    args = parser.parse_args()
    for name in ('width', 'height'):
        if getattr(args, name) is not None and getattr(args, name) < 200:
            parser.error(f'--{name} 不能小于 200')
    if len(args.wish) > 24:
        parser.error('--wish 最多 24 字')
    return args


def main():
    args = parse_args()
    if sys.platform != 'win32':
        raise SystemExit('桌面悬浮模式目前支持 Windows；其他系统可打开 index.html。')
    app = QApplication(sys.argv[:1])
    app.setQuitOnLastWindowClosed(False)
    try:
        window = Overlay(args)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    window.show()
    hotkeys = Hotkeys(window)
    app.installNativeEventFilter(hotkeys)
    app.aboutToQuit.connect(hotkeys.close)
    tray = QSystemTrayIcon(tray_icon(), app)
    tray.setToolTip('星愿 · Ctrl+Alt+Shift+Q 退出')
    menu = QMenu()
    for label, callback in [
        ('重播开场  Ctrl+Alt+Shift+R', window.restart),
        ('星光绽放  Ctrl+Alt+Shift+B', window.burst),
        ('隐藏 / 显示  Ctrl+Alt+Shift+H', window.toggle_visibility),
        ('退出  Ctrl+Alt+Shift+Q', app.quit),
    ]:
        action = QAction(label, menu)
        action.triggered.connect(callback)
        menu.addAction(action)
    tray.setContextMenu(menu)
    tray.show()
    if hotkeys.failed:
        tray.showMessage('部分快捷键被占用', '、'.join(hotkeys.failed) + '；可使用托盘菜单操作。')
    result = app.exec()
    # Dispose of the web view before its underlying Chromium profile.
    window.close()
    return result


if __name__ == '__main__':
    sys.exit(main())
