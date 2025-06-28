<<<<<<< HEAD
## **UPD!!!** **A demo of Manga Colorization v2.5 is now available [link](https://mangacol.com). Feel free to check it out!**
=======
# 漫画自动上色工具 Manga Colorization GUI
>>>>>>> c061684 (Update readme.md)

## 项目简介
本项目为高质量漫画/线稿自动上色工具，支持批量处理、单图处理、DPI/分辨率/色彩微调、去噪、GPU/MPS加速、参数模板管理、深浅色主题自适应等。界面美观，参数可配置，适合批量汉化、同人上色、AI辅助等场景。

## 权重下载
- 生成器权重：[generator.zip](https://drive.google.com/file/d/1qmxUEKADkEM4iYLp1fpPLLKnfZ6tcF-t/view?usp=sharing) → 放入 `networks/`
- 特征提取器权重：`extractor.pth`（随项目或同上） → 放入 `networks/`
- 去噪权重：[net_rgb.pth](https://drive.google.com/file/d/161oyQcYpdkVdw8gKz_MA8RD-Wtg9XDp3/view?usp=sharing) → 放入 `denoising/models/`

## 环境依赖
- Python 3.8+
- 推荐使用 macOS/Linux/Windows，支持M1/M2/Intel/NVIDIA GPU
- 主要依赖：torch、torchvision、opencv-python、matplotlib、tkinter 等
- 安装依赖：
```bash
pip install -r requirements.txt
```

## 快速使用
### 1. 批量上色（推荐）
```bash
python gui.py
```
- 图形界面支持批量/单图处理、参数模板、日志输出、任务终止、深浅色自适应。
- 支持“按原图分辨率输出”与“手动输入尺寸”互斥，参数链路已打通。

### 2. 命令行批量/单图上色
```bash
python inference.py -p "图片或文件夹路径"
```
- 其他常用参数：
  - `-sd` 输出目录（默认./colorized）
  - `-s` 处理分辨率（32的倍数，默认576）
  - `-ds` 去噪强度（默认25）
  - `--no_denoise` 关闭去噪
  - `--no_hue_sat_adjust` 关闭色相/饱和度微调
  - `--dpi` 输出DPI（默认300）
  - `-g` 使用NVIDIA GPU
  - `--hue_shift` 色相微调
  - `--sat_shift` 饱和度微调

### 3. 处理效果示例
| 原图      | 上色结果      |
|------------|-------------|
| <img src="figures/bw1.jpg" width="256"> | <img src="figures/color1.png" width="256"> |
| <img src="figures/bw2.jpg" width="256"> | <img src="figures/color2.png" width="256"> |
| <img src="figures/bw3.jpg" width="256"> | <img src="figures/color3.png" width="256"> |

## 参数说明
- 支持DPI、分辨率、去噪、色相/饱和度微调、GPU/MPS、模板管理等。
- “按原图分辨率输出”与“手动输入尺寸”互斥，前端互斥、后端只用size。
- 所有参数可通过GUI或命令行灵活配置。

## 常见问题
- **通道数报错/偏色**：请确保权重和依赖正确，且未手动多次调用 update_hint。
- **图片尺寸报错**：请确保输入尺寸为32的倍数，或勾选“按原图分辨率输出”。
- **模型推理慢**：建议使用GPU/MPS加速，或适当降低分辨率。
- **界面卡顿/闪退**：请升级Python和依赖，或尝试命令行模式。

## 交流与反馈
- 项目主页：[https://github.com/opanded/manga-colorization-GUI](https://github.com/opanded/manga-colorization-GUI)
- 问题反馈：请在GitHub issue区提交详细报错和环境信息。

---

> 本项目仅供学术交流与个人研究使用，严禁用于任何商业用途。
