# 星愿 · Starlit Christmas

## Windows 桌面悬浮模式

透明背景、无边框、始终置顶。粒子直接叠加在编辑器等应用上方，鼠标穿透，可以继续点击、输入和滚动下方应用；不显示黑色底板或任务栏窗口。右下角系统托盘提供控制菜单。

安装 Python 3.10+ 后，在本目录运行：

```sh
python -m pip install -r requirements.txt
python overlay.py
```

也可双击 `launch_overlay.pyw`（需系统的 Python 文件关联指向已安装 PySide6 的环境）。

- `Ctrl+Alt+Shift+R`：重播开场。
- `Ctrl+Alt+Shift+B`：星光绽放。
- `Ctrl+Alt+Shift+H`：隐藏 / 显示。
- `Ctrl+Alt+Shift+Q`：退出。

默认位于主屏幕右侧。可以指定尺寸、位置、屏幕、配色与祝福：

```sh
python overlay.py --width 760 --height 900 --x 900 --y 80 --theme gold --wish "愿所有美好，如期而至"
```

位置与尺寸使用逻辑像素；`--screen 1` 选择第二块屏幕。悬浮模式的快捷键是全局快捷键，操作时无需离开编辑器；若快捷键被其他软件占用，请使用系统托盘菜单。退出后会释放快捷键。

## 浏览器模式

零依赖的实时 WebGL 粒子圣诞树。双击 `index.html`，用 Chrome 或 Edge 打开即可，无需安装依赖或联网。需要浏览器支持 WebGL 并启用硬件加速。

- 金色立体粒子圣诞树、螺旋灯带、五角星光晕、飘雪、地面星环。
- 约 5 秒粒子汇聚开场，随后持续旋转；可切换冰雪蓝、修改祝福语。
- `R` 重播开场，`B` 星光绽放，`H` 隐藏/显示控件，空格暂停/继续，`Esc` 恢复控件。
- 全屏按钮或浏览器 `F11`，支持纯净画面。
- “导出竖屏”生成 20 秒、1080×1920、30fps 的 WebM 动画，无音轨。实际帧率取决于电脑图形与编码性能；导出时保持页面在前台。
- 支持系统减少动态效果偏好：预览默认静态；点击导出时仍生成完整动画。

也可以使用任意静态 HTTP 服务运行，例如 `python -m http.server 8080`，然后打开 http://localhost:8080 。

原生 JavaScript、WebGL 1.0 与 Canvas 2D；自定义 GLSL 粒子着色器、加法混合、分层树枝及螺旋灯带几何。固定随机种子保证初始几何可复现。资源内置于单个 HTML 文件，无外部字体、素材、CDN 或统计服务。导出在本地完成，不上传数据。

License: [MIT](LICENSE)。
