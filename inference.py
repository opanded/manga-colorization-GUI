# 本脚本用于批量为漫画图片进行自动上色处理。
# 支持递归处理多级目录，自动按原始目录结构保存结果。
# 支持 Apple M1/M2 (mps)、NVIDIA GPU (cuda)、CPU 三种加速模式。
# 主要参数可通过命令行传入。

import os
import argparse
import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt
from colorizator import MangaColorizator
import sys

# 获取输出图片的相对路径，保证输出结构与输入一致
# input_path: 输入图片绝对路径
# root_path: 输入根目录
# save_dir: 输出根目录
# 返回：输出图片的完整路径

def get_relative_save_path(input_path, root_path, save_dir):
    """
    根据输入图片路径、根目录和保存目录，生成合理的输出路径。
    """
    rel_path = os.path.relpath(input_path, root_path)
    rel_dir = os.path.dirname(rel_path)
    save_folder = os.path.join(save_dir, rel_dir)
    os.makedirs(save_folder, exist_ok=True)
    save_path = os.path.join(save_folder, os.path.basename(input_path))
    return save_path

# 处理单张图片的上色流程
# image_path: 输入图片路径
# save_path: 输出图片路径
# colorizator: 上色模型对象
# args: 参数对象

def colorize_single_image(image_path, save_path, colorizator, args):
    if os.path.exists(save_path):
        print(f"已存在，无需重复处理: {save_path}", flush=True)
        return
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"无法读取图片: {image_path}", flush=True)
            return
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        colorizator.set_image(image, args.size, args.denoiser, args.denoiser_sigma)
        # 默认开启色相/饱和度微调，除非用户指定 --no_hue_sat_adjust
        adjust_hue_saturation = not getattr(args, 'no_hue_sat_adjust', False)
        colorization = colorizator.colorize(
            adjust_hue_saturation=adjust_hue_saturation,
            hue_delta=getattr(args, 'hue_shift', 0.02),
            sat_delta=getattr(args, 'sat_shift', -0.10)
        )
        plt.imsave(save_path, colorization, dpi=getattr(args, 'dpi', 300))
        print(f"已保存: {save_path}", flush=True)
    except Exception as e:
        print(f"处理图片 {image_path} 时出错: {str(e)}", flush=True)

# 批量递归处理目录下所有图片
# path: 输入目录
# colorizator: 上色模型对象
# args: 参数对象

def colorize_images(path, colorizator, args):
    print(f"正在处理目录: {path}", flush=True)
    for root, dirs, files in os.walk(path):
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        image_files = [f for f in files if os.path.splitext(f)[1].lower() in image_extensions]
        for file in sorted(image_files):
            file_path = os.path.join(root, file)
            save_path = get_relative_save_path(file_path, path, args.save_dir)
            # 检查输出目录中是否已存在同名文件
            if os.path.exists(save_path):
                print(f"已存在，无需重复处理: {save_path}", flush=True)
                continue
            print(f"正在处理图片: {file_path}", flush=True)
            colorize_single_image(file_path, save_path, colorizator, args)

# 解析命令行参数
# 支持自定义输入路径、模型路径、是否用GPU、去噪参数、输出目录、图片尺寸等

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', required=True, help='图片或文件夹路径')
    parser.add_argument("-gen", "--generator", default = 'networks/generator.zip', help='生成器模型路径')
    parser.add_argument("-ext", "--extractor", default = 'networks/extractor.pth', help='特征提取器模型路径')
    parser.add_argument('-g', '--gpu', dest = 'gpu', action = 'store_true', help='使用NVIDIA GPU')
    parser.add_argument('-nd', '--no_denoise', dest = 'denoiser', action = 'store_false', help='不使用去噪')
    parser.add_argument('-d', '--denoiser', action='store_true', help='使用去噪器')
    parser.add_argument('-ds', '--denoiser_sigma', type=float, default=25, help='去噪器的sigma值')
    parser.add_argument('-sd', '--save_dir', type=str, default='./colorized', help='保存结果的目录')
    parser.add_argument("-s", "--size", type = int, default = 576, help='图片处理尺寸')
    # parser.add_argument('--keep_ratio', action='store_true', help='按原图分辨率输出，仅补pad到32倍数，与size互斥')
    parser.add_argument('--no_hue_sat_adjust', action='store_true', help='关闭色相+0.02/饱和度-0.10微调（默认开启）')
    parser.add_argument('--dpi', type=int, default=300, help='输出图片DPI')
    parser.add_argument('--hue_shift', type=float, default=0.02, help='色相微调，默认0.02')
    parser.add_argument('--sat_shift', type=float, default=-0.10, help='饱和度微调，默认-0.10')
    parser.set_defaults(gpu = False)
    parser.set_defaults(denoiser = True)
    args = parser.parse_args()
    return args

# 主流程入口，自动检测设备，初始化模型，批量处理图片
if __name__ == "__main__":
    args = parse_args()
    print("开始处理图片任务...", flush=True)
    print("输入路径:", args.path, flush=True)
    if not os.path.exists(args.path):
        print("输入路径不存在！请检查路径是否正确。", flush=True)
    else:
        files = os.listdir(args.path)
        print("目录下文件:", files, flush=True)
    # 设备选择优化，优先支持 mps（Apple Silicon），否则 GPU，再否则 CPU
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = 'mps'
        print("检测到 Apple 芯片，使用 MPS 加速模式。", flush=True)
    elif args.gpu:
        device = 'cuda'
        print("使用 CUDA GPU 加速模式。", flush=True)
    else:
        device = 'cpu'
        print("使用 CPU 模式。", flush=True)
    colorizer = MangaColorizator(device, args.generator, args.extractor)
    if os.path.isdir(args.path):
        colorize_images(args.path, colorizer, args)
    elif os.path.isfile(args.path):
        split = os.path.splitext(args.path)
        if split[1].lower() in ('.jpg', '.png', '.jpeg'):
            save_path = get_relative_save_path(args.path, os.path.dirname(args.path), args.save_dir)
            colorize_single_image(args.path, save_path, colorizer, args)
        else:
            print('文件格式不支持，仅支持图片文件。', flush=True)
    else:
        print('输入路径无效，请检查。', flush=True)

