import numpy as np
import cv2

def resize_pad(img, size = None):
    if size is None:
        # 若未指定 size，使用原始图像的最大边长
        size = max(img.shape[0], img.shape[1])
    # 使size为32的倍数
    if size % 32 != 0:
        size = ((size // 32) + 1) * 32
    # 缩放短边到size，长边等比例缩放
    h, w = img.shape[:2]
    if h < w:
        new_h = size
        new_w = int(w * (size / h))
    else:
        new_w = size
        new_h = int(h * (size / w))
    img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    if len(img.shape) == 2:
        img = np.expand_dims(img, 2)
    if img.shape[2] == 1:
        img = np.repeat(img, 3, 2)
    if img.shape[2] == 4:
        img = img[:, :, :3]
    pad = None
    # 确保高度和宽度都能被32整除，pad到最近的32倍数
    new_height = img.shape[0] + (32 - img.shape[0] % 32) if img.shape[0] % 32 != 0 else img.shape[0]
    new_width = img.shape[1] + (32 - img.shape[1] % 32) if img.shape[1] % 32 != 0 else img.shape[1]
    pad = (new_height - img.shape[0], new_width - img.shape[1])
    img = np.pad(img, ((0, pad[0]), (0, pad[1]), (0, 0)), 'maximum')
    if img.dtype == 'float32':
        np.clip(img, 0, 1, out = img)
    return img, pad