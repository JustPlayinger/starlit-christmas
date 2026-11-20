"""Double-click launcher without a console window."""
import sys

try:
    from overlay import main
except ImportError:
    import ctypes
    ctypes.windll.user32.MessageBoxW(
        None,
        '缺少 PySide6。请在此目录打开终端，运行：\npython -m pip install -r requirements.txt\n\n然后运行 python overlay.py。',
        '星愿 · 依赖未安装',
        0x10,
    )
    sys.exit(1)

sys.exit(main())
