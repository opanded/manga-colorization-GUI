import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
import webbrowser
import threading
import subprocess
import shutil
import tempfile

TEMPLATE_FILE = 'gui_templates.json'

# 默认参数模板
def get_default_params():
    return {
        'input_path': '',
        'output_path': './colorized',
        'size': 576,
        'denoiser': True,
        'denoiser_sigma': 25,
        'hue_sat_adjust': True,
        'hue_shift': 0.02,
        'sat_shift': -0.10,
        'gpu': False,
        'mps': True,
        'generator': 'networks/generator.zip',
        'extractor': 'networks/extractor.pth',
        'dpi': 300
    }

def load_templates():
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_templates(templates):
    with open(TEMPLATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)
    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 30
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left', background="#222", fg="#fff", relief='solid', borderwidth=1, font=("微软雅黑", 10))
        label.pack(ipadx=1)
    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class MangaColorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('漫画上色批量处理工具')
        self.root.attributes('-topmost', True)  # 窗口始终置顶
        self.templates = load_templates()
        self.current_params = get_default_params()
        self.create_widgets()
        self.set_params_to_ui(get_default_params())
        self.refresh_template_list()
        self.subprocesses = []  # 保存所有子进程
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
    def __init__(self, root):
        self.root = root
        self.root.title('漫画上色批量处理工具')
        self.root.attributes('-topmost', True)  # 窗口始终置顶
        self.templates = load_templates()
        self.current_params = get_default_params()
        self.create_widgets()
        self.set_params_to_ui(get_default_params())
        self.refresh_template_list()
        self.subprocesses = []  # 保存所有子进程
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def on_close(self):
        # 关闭窗口时主动终止所有子进程
        for p in self.subprocesses:
            try:
                if p.poll() is None:
                    p.terminate()
            except Exception:
                pass
        self.root.destroy()

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#222', foreground='#fff', fieldbackground='#222')
        style.configure('TLabel', background='#222', foreground='#fff')
        style.configure('TButton', background='#444', foreground='#fff')
        style.configure('TCheckbutton', background='#222', foreground='#fff')
        style.configure('TEntry', fieldbackground='#222', foreground='#fff')
        style.map('TButton', background=[('active', '#333')])

        nb = ttk.Notebook(self.root)
        nb.pack(fill='both', expand=True, padx=10, pady=10)
        # 批量处理页
        main_frm = ttk.Frame(nb)
        nb.add(main_frm, text='批量处理')
        # 处理图像页
        single_frm = ttk.Frame(nb)
        nb.add(single_frm, text='处理图像')
        # 高级参数页
        adv_frm = ttk.Frame(nb)
        nb.add(adv_frm, text='高级选项')
        # 按原图比例输出选项（必须先于toggle_keep_ratio调用）
        self.keep_ratio_var = tk.BooleanVar(value=False)
        # 批量处理页布局
        btn_recent = tk.Button(main_frm, text='加载最近模板', bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove', command=self.load_recent_template)
        btn_recent.grid(row=0, column=0, sticky='ew', padx=2, pady=2)
        ToolTip(btn_recent, '一键加载最近保存的模板参数')
        # 输入路径
        tk.Label(main_frm, text='输入路径:').grid(row=1, column=0, sticky='e', padx=2, pady=2)
        self.input_entry = tk.Entry(main_frm, width=40, bg='#222', fg='#fff', insertbackground='#fff')
        self.input_entry.grid(row=1, column=1, sticky='ew', padx=(2,2), pady=2)
        btn_in = tk.Button(main_frm, text='选择', command=self.choose_input, bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove')
        btn_in.grid(row=1, column=2, sticky='ew', padx=(2,10), pady=2)
        ToolTip(btn_in, '选择需要上色的图片文件夹或单张图片')
        # 输出路径
        tk.Label(main_frm, text='输出路径:').grid(row=2, column=0, sticky='e', padx=2, pady=2)
        self.output_entry = tk.Entry(main_frm, width=40, bg='#222', fg='#fff', insertbackground='#fff')
        self.output_entry.grid(row=2, column=1, sticky='ew', padx=(2,2), pady=2)
        btn_out = tk.Button(main_frm, text='选择', command=self.choose_output, bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove')
        btn_out.grid(row=2, column=2, sticky='ew', padx=(2,10), pady=2)
        ToolTip(btn_out, '选择上色后图片的保存文件夹')
        # 批量处理按钮
        btn_run = tk.Button(main_frm, text='开始批量处理', command=self.run_batch, bg='#e0e0e0', fg='#111111', font=('微软雅黑', 12, 'bold'), activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove')
        btn_run.grid(row=3, column=1, pady=10, sticky='ew')
        ToolTip(btn_run, '根据当前参数批量上色。')
        # 终止任务按钮
        btn_stop = tk.Button(main_frm, text='终止任务', bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove', command=self.stop_batch)
        btn_stop.grid(row=3, column=2, pady=10, sticky='ew')
        ToolTip(btn_stop, '强制终止当前批量处理任务')
        # 日志输出框
        tk.Label(main_frm, text='运行日志:').grid(row=4, column=0, sticky='ne', padx=2, pady=2)
        self.log_text = tk.Text(main_frm, height=12, width=60, bg='#111', fg='#fff', insertbackground='#fff', state='disabled')
        self.log_text.grid(row=4, column=1, columnspan=3, sticky='nsew', padx=2, pady=2)
        main_frm.columnconfigure(1, weight=1)
        main_frm.columnconfigure(2, weight=0)
        main_frm.rowconfigure(4, weight=1)
        # 处理图像页布局（单图像处理）
        btn_single_recent = tk.Button(single_frm, text='加载最近模板', bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove', command=self.load_recent_template)
        btn_single_recent.grid(row=0, column=0, sticky='ew', padx=2, pady=2)
        ToolTip(btn_single_recent, '一键加载最近保存的模板参数')
        tk.Label(single_frm, text='输入图像:').grid(row=1, column=0, sticky='e', padx=2, pady=2)
        self.single_input_entry = tk.Entry(single_frm, width=40, bg='#222', fg='#fff', insertbackground='#fff')
        self.single_input_entry.grid(row=1, column=1, sticky='ew', padx=(2,2), pady=2)
        btn_single_in = tk.Button(single_frm, text='选择', command=self.choose_single_input, bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove')
        btn_single_in.grid(row=1, column=2, sticky='ew', padx=(2,10), pady=2)
        ToolTip(btn_single_in, '选择需要上色的单张图片')
        tk.Label(single_frm, text='输出路径:').grid(row=2, column=0, sticky='e', padx=2, pady=2)
        self.single_output_entry = tk.Entry(single_frm, width=40, bg='#222', fg='#fff', insertbackground='#fff')
        self.single_output_entry.grid(row=2, column=1, sticky='ew', padx=(2,2), pady=2)
        btn_single_out = tk.Button(single_frm, text='选择', command=self.choose_single_output, bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove')
        btn_single_out.grid(row=2, column=2, sticky='ew', padx=(2,10), pady=2)
        ToolTip(btn_single_out, '选择上色后图片的保存文件夹')
        # 移除DPI输入框
        btn_single_run = tk.Button(single_frm, text='处理图像', command=self.run_single, bg='#e0e0e0', fg='#111111', font=('微软雅黑', 12, 'bold'), activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove')
        btn_single_run.grid(row=3, column=1, pady=10, sticky='ew')
        ToolTip(btn_single_run, '对当前图片进行上色处理。')
        btn_single_stop = tk.Button(single_frm, text='终止处理', bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove', command=self.stop_batch)
        btn_single_stop.grid(row=3, column=2, pady=10, sticky='ew')
        ToolTip(btn_single_stop, '强制终止当前处理任务')
        tk.Label(single_frm, text='运行日志:').grid(row=4, column=0, sticky='ne', padx=2, pady=2)
        self.single_log_text = tk.Text(single_frm, height=12, width=60, bg='#111', fg='#fff', insertbackground='#fff', state='disabled')
        self.single_log_text.grid(row=4, column=1, columnspan=2, sticky='nsew', padx=2, pady=2)
        single_frm.columnconfigure(1, weight=1)
        single_frm.columnconfigure(2, weight=0)
        single_frm.rowconfigure(4, weight=1)

        # 高级参数（危险提示）
        tk.Label(adv_frm, text='⚠️ 高级参数请谨慎修改，错误设置可能导致程序无法运行！', foreground='orange', background='#222', font=('微软雅黑', 10, 'bold')).grid(row=0, column=0, columnspan=4, pady=8)
        self.denoise_var = tk.BooleanVar(value=True)
        chk_denoise = tk.Checkbutton(adv_frm, text='使用去噪', variable=self.denoise_var, bg='#222', fg='#fff', selectcolor='#444', activebackground='#333')
        chk_denoise.grid(row=1, column=0, sticky='w')
        ToolTip(chk_denoise, '勾选可减少杂色，推荐开启。图片本身很干净时可关闭。')
        tk.Label(adv_frm, text='去噪sigma:').grid(row=1, column=1, sticky='e')
        self.sigma_entry = tk.Entry(adv_frm, width=8, bg='#222', fg='#fff', insertbackground='#fff')
        self.sigma_entry.grid(row=1, column=2, sticky='w')
        ToolTip(self.sigma_entry, '去噪强度，数值越大去噪越强，默认25。高ISO扫描件可适当提高。')
        # 色相/饱和度微调参数（合并逻辑：开关控制输入框可用性）
        self.hue_sat_var = tk.BooleanVar(value=True)
        chk_hue = tk.Checkbutton(adv_frm, text='启用色相/饱和度微调', variable=self.hue_sat_var, bg='#222', fg='#fff', selectcolor='#444', activebackground='#333', command=self.toggle_hue_sat_entries)
        chk_hue.grid(row=2, column=0, sticky='w')
        ToolTip(chk_hue, '开启后可自定义色相/饱和度微调参数。关闭则不做色彩微调。')
        tk.Label(adv_frm, text='输出DPI:').grid(row=2, column=1, sticky='e')
        self.dpi_entry = tk.Entry(adv_frm, width=8, bg='#222', fg='#fff', insertbackground='#fff')
        self.dpi_entry.insert(0, '300')
        self.dpi_entry.grid(row=2, column=2, sticky='w')
        ToolTip(self.dpi_entry, '输出图片的DPI，常用300/600/1200。仅影响图片元数据，不改变像素。')
        tk.Label(adv_frm, text='图片尺寸:').grid(row=3, column=0, sticky='e')
        self.size_entry = tk.Entry(adv_frm, width=10, bg='#222', fg='#fff', insertbackground='#fff')
        self.size_entry.insert(0, '576')
        self.size_entry.grid(row=3, column=1, sticky='w')
        ToolTip(self.size_entry, '处理分辨率，建议576，需为32的倍数。尺寸越大，细节越多但速度越慢。与“按原图分辨率输出”互斥。')
        # keep_ratio 互斥选项控件
        chk_keep_ratio = tk.Checkbutton(adv_frm, text='按原图分辨率输出（推荐高质量还原）', variable=self.keep_ratio_var, bg='#222', fg='#fff', selectcolor='#444', activebackground='#333', command=self.toggle_keep_ratio)
        chk_keep_ratio.grid(row=3, column=2, sticky='w', padx=(10,0))
        ToolTip(chk_keep_ratio, '勾选后输出分辨率与原图一致，仅补齐到32倍数，图像尺寸输入将被禁用。')

        # GPU/MPS 选项
        self.gpu_var = tk.BooleanVar(value=False)
        self.mps_var = tk.BooleanVar(value=True)
        chk_gpu = tk.Checkbutton(adv_frm, text='NVIDIA GPU', variable=self.gpu_var, bg='#222', fg='#fff', selectcolor='#444', activebackground='#333')
        chk_gpu.grid(row=6, column=0, sticky='w')
        ToolTip(chk_gpu, '仅Windows/NVIDIA显卡可用。M1/M2用户请勿勾选。')
        chk_mps = tk.Checkbutton(adv_frm, text='Apple M1/M2加速', variable=self.mps_var, bg='#222', fg='#fff', selectcolor='#444', activebackground='#333')
        chk_mps.grid(row=6, column=1, sticky='w')
        ToolTip(chk_mps, 'Mac用户建议勾选。Windows用户请勿勾选。')

        # 模板管理
        tk.Label(adv_frm, text='模板名称:').grid(row=7, column=0, sticky='e')
        self.template_name_entry = tk.Entry(adv_frm, width=20, bg='#222', fg='#fff', insertbackground='#fff')
        self.template_name_entry.grid(row=7, column=1, sticky='w')
        btn_save = tk.Button(adv_frm, text='保存模板', command=self.save_template, bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove')
        btn_save.grid(row=7, column=2)
        ToolTip(btn_save, '保存当前参数为新模板，便于下次快速调用。')
        btn_update = tk.Button(adv_frm, text='更新模板', command=self.update_template, bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove')
        # 清理toggle_keep_ratio残留无用代码，确保只做状态切换
        ToolTip(btn_update, '将当前参数覆盖到选中的模板，无需删除再新建。')
        btn_del = tk.Button(adv_frm, text='删除模板', command=self.delete_template, bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove')
        btn_del.grid(row=7, column=4)
        ToolTip(btn_del, '删除选中的模板。')
        tk.Label(adv_frm, text='模板列表:').grid(row=8, column=0, sticky='ne')
        self.template_listbox = tk.Listbox(adv_frm, height=5, width=30, bg='#222', fg='#fff', selectbackground='#444')
        self.template_listbox.grid(row=8, column=1, sticky='nsew', padx=2, pady=2)
        btn_load = tk.Button(adv_frm, text='加载模板', command=self.load_template, bg='#e0e0e0', fg='#111111', activebackground='#cccccc', activeforeground='#111111', highlightbackground='#cccccc', highlightcolor='#111111', borderwidth=2, relief='groove')
        btn_load.grid(row=8, column=2, sticky='ew', padx=2, pady=2)
        ToolTip(btn_load, '加载选中的模板参数。')
        help_label = tk.Label(adv_frm, text='使用说明', fg='skyblue', bg='#222', cursor='hand2')
        help_label.grid(row=9, column=1)
        help_label.bind('<Button-1>', lambda e: webbrowser.open('https://github.com/manga-colorization-GUI'))
        ToolTip(help_label, '点击查看详细使用说明和常见问题。')

        # 高级参数页自适应布局
        for i in range(5):
            adv_frm.columnconfigure(i, weight=1)
        for i in range(9):
            adv_frm.rowconfigure(i, weight=0)
        adv_frm.rowconfigure(8, weight=1)

        # 色相/饱和度微调参数（受开关控制）
        tk.Label(adv_frm, text='色相微调:').grid(row=4, column=0, sticky='e')
        self.hue_entry = tk.Entry(adv_frm, width=8, bg='#222', fg='#fff', insertbackground='#fff')
        self.hue_entry.insert(0, '0.02')
        self.hue_entry.grid(row=4, column=1, sticky='w')
        ToolTip(self.hue_entry, '色相微调，默认0.02，调节色彩偏移。仅在启用微调时生效。')
        tk.Label(adv_frm, text='饱和度微调:').grid(row=4, column=2, sticky='e')
        self.sat_entry = tk.Entry(adv_frm, width=8, bg='#222', fg='#fff', insertbackground='#fff')
        self.sat_entry.insert(0, '-0.10')
        self.sat_entry.grid(row=4, column=3, sticky='w')
        ToolTip(self.sat_entry, '饱和度微调，默认-0.10，调节色彩浓淡。仅在启用微调时生效。')
        # 初始化微调输入框状态
        self.toggle_hue_sat_entries()

        # keep_ratio互斥逻辑初始化
        self.toggle_keep_ratio()

    def toggle_keep_ratio(self):
        # 互斥逻辑：勾选则禁用size输入框
        if hasattr(self, 'size_entry'):
            if self.keep_ratio_var.get():
                self.size_entry.config(state='disabled')
            else:
                self.size_entry.config(state='normal')

    def toggle_hue_sat_entries(self):
        state = 'normal' if self.hue_sat_var.get() else 'disabled'
        self.hue_entry.config(state=state)
        self.sat_entry.config(state=state)

    def choose_input(self):
        path = filedialog.askdirectory() or ''
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, path)

    def choose_output(self):
        path = filedialog.askdirectory() or ''
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, path)

    def choose_single_input(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")]) or ''
        self.single_input_entry.delete(0, tk.END)
        self.single_input_entry.insert(0, path)

    def choose_single_output(self):
        path = filedialog.askdirectory() or ''
        self.single_output_entry.delete(0, tk.END)
        self.single_output_entry.insert(0, path)

    def save_template(self):
        name = self.template_name_entry.get().strip()
        if not name:
            messagebox.showwarning('提示', '请输入模板名称')
            return
        params = self.get_params_from_ui()
        self.templates[name] = params
        save_templates(self.templates)
        self.refresh_template_list()
        messagebox.showinfo('提示', '模板已保存')

    def update_template(self):
        sel = self.template_listbox.curselection()
        if not sel:
            messagebox.showwarning('提示', '请选择要更新的模板')
            return
        name = self.template_listbox.get(sel[0])
        params = self.get_params_from_ui()
        self.templates[name] = params
        save_templates(self.templates)
        self.refresh_template_list()
        messagebox.showinfo('提示', f'模板“{name}”已更新')

    def delete_template(self):
        sel = self.template_listbox.curselection()
        if not sel:
            messagebox.showwarning('提示', '请选择要删除的模板')
            return
        name = self.template_listbox.get(sel[0])
        if name in self.templates:
            del self.templates[name]
            save_templates(self.templates)
            self.refresh_template_list()
            messagebox.showinfo('提示', '模板已删除')

    def load_template(self):
        sel = self.template_listbox.curselection()
        if not sel:
            messagebox.showwarning('提示', '请选择要加载的模板')
            return
        name = self.template_listbox.get(sel[0])
        params = self.templates.get(name, get_default_params())
        self.set_params_to_ui(params)

    def load_recent_template(self):
        if self.templates:
            # 取最后一个保存的模板
            last_name = list(self.templates.keys())[-1]
            params = self.templates[last_name]
            self.set_params_to_ui(params)
            messagebox.showinfo('提示', f'已加载最近模板：{last_name}')
        else:
            messagebox.showinfo('提示', '暂无历史模板可加载')

    def refresh_template_list(self):
        self.template_listbox.delete(0, tk.END)
        for name in self.templates:
            self.template_listbox.insert(tk.END, name)

    def set_params_to_ui(self, params):
        # 批量处理页
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, params.get('input_path', ''))
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, params.get('output_path', './colorized'))
        # 处理图像页
        if hasattr(self, 'single_input_entry'):
            self.single_input_entry.delete(0, tk.END)
            self.single_input_entry.insert(0, params.get('input_path', ''))
        if hasattr(self, 'single_output_entry'):
            self.single_output_entry.delete(0, tk.END)
            self.single_output_entry.insert(0, params.get('output_path', './colorized'))
        # 高级参数
        if hasattr(self, 'size_entry'):
            self.size_entry.delete(0, tk.END)
            self.size_entry.insert(0, str(params.get('size', 576)))
        if hasattr(self, 'keep_ratio_var'):
            self.keep_ratio_var.set(params.get('keep_ratio', False))
            self.toggle_keep_ratio()
        if hasattr(self, 'denoise_var'):
            self.denoise_var.set(params.get('denoiser', True))
        if hasattr(self, 'sigma_entry'):
            self.sigma_entry.delete(0, tk.END)
            self.sigma_entry.insert(0, str(params.get('denoiser_sigma', 25)))
        if hasattr(self, 'hue_sat_var'):
            self.hue_sat_var.set(params.get('hue_sat_adjust', True))
        if hasattr(self, 'gen_entry'):
            self.gen_entry.delete(0, tk.END)
            self.gen_entry.insert(0, params.get('generator', 'networks/generator.zip'))
        if hasattr(self, 'ext_entry'):
            self.ext_entry.delete(0, tk.END)
            self.ext_entry.insert(0, params.get('extractor', 'networks/extractor.pth'))
        if hasattr(self, 'gpu_var'):
            self.gpu_var.set(params.get('gpu', False))
        if hasattr(self, 'mps_var'):
            self.mps_var.set(params.get('mps', True))
        if hasattr(self, 'dpi_entry'):
            self.dpi_entry.delete(0, tk.END)
            self.dpi_entry.insert(0, str(params.get('dpi', 300)))
        # 高级参数页色相/饱和度微调可调节
        if hasattr(self, 'hue_entry'):
            self.hue_entry.delete(0, tk.END)
            self.hue_entry.insert(0, str(params.get('hue_shift', 0.02)))
        if hasattr(self, 'sat_entry'):
            self.sat_entry.delete(0, tk.END)
            self.sat_entry.insert(0, str(params.get('sat_shift', -0.10)))

    def get_params_from_ui(self):
        keep_ratio = self.keep_ratio_var.get() if hasattr(self, 'keep_ratio_var') else False
        if keep_ratio:
            size_val = 576  # 实际不会用到
        else:
            try:
                size_val = int(getattr(self, 'size_entry', tk.Entry()).get() or 576)
            except Exception:
                size_val = 576
            if size_val % 32 != 0:
                size_val = ((size_val // 32) + 1) * 32
                if hasattr(self, 'size_entry'):
                    self.size_entry.delete(0, tk.END)
                    self.size_entry.insert(0, str(size_val))
        return {
            'input_path': self.input_entry.get().strip(),
            'output_path': self.output_entry.get().strip(),
            'size': size_val,
            'keep_ratio': keep_ratio,
            'denoiser': self.denoise_var.get() if hasattr(self, 'denoise_var') else True,
            'denoiser_sigma': float(getattr(self, 'sigma_entry', tk.Entry()).get() or 25),
            'hue_sat_adjust': self.hue_sat_var.get() if hasattr(self, 'hue_sat_var') else True,
            'hue_shift': float(self.hue_entry.get() or 0.02),
            'sat_shift': float(self.sat_entry.get() or -0.10),
            'generator': self.gen_entry.get().strip() if hasattr(self, 'gen_entry') else 'networks/generator.zip',
            'extractor': self.ext_entry.get().strip() if hasattr(self, 'ext_entry') else 'networks/extractor.pth',
            'gpu': self.gpu_var.get() if hasattr(self, 'gpu_var') else False,
            'mps': self.mps_var.get() if hasattr(self, 'mps_var') else True,
            'dpi': int(self.dpi_entry.get() or 300)
        }
    def get_single_params_from_ui(self):
        keep_ratio = self.keep_ratio_var.get() if hasattr(self, 'keep_ratio_var') else False
        if keep_ratio:
            size_val = 576  # 实际不会用到
        else:
            try:
                size_val = int(getattr(self, 'size_entry', tk.Entry()).get() or 576)
            except Exception:
                size_val = 576
            if size_val % 32 != 0:
                size_val = ((size_val // 32) + 1) * 32
                if hasattr(self, 'size_entry'):
                    self.size_entry.delete(0, tk.END)
                    self.size_entry.insert(0, str(size_val))
        return {
            'input_path': self.single_input_entry.get().strip(),
            'output_path': self.single_output_entry.get().strip(),
            'size': size_val,
            'keep_ratio': keep_ratio,
            'denoiser': self.denoise_var.get() if hasattr(self, 'denoise_var') else True,
            'denoiser_sigma': float(getattr(self, 'sigma_entry', tk.Entry()).get() or 25),
            'hue_sat_adjust': self.hue_sat_var.get() if hasattr(self, 'hue_sat_var') else True,
            'hue_shift': float(self.hue_entry.get() or 0.02),
            'sat_shift': float(self.sat_entry.get() or -0.10),
            'generator': self.gen_entry.get().strip() if hasattr(self, 'gen_entry') else 'networks/generator.zip',
            'extractor': self.ext_entry.get().strip() if hasattr(self, 'ext_entry') else 'networks/extractor.pth',
            'gpu': self.gpu_var.get() if hasattr(self, 'gpu_var') else False,
            'mps': self.mps_var.get() if hasattr(self, 'mps_var') else True,
            'dpi': int(self.dpi_entry.get() or 300)
        }

    def run_batch(self):
        params = self.get_params_from_ui()
        # 参数自检
        errors = []
        if not params['input_path'] or not os.path.exists(params['input_path']):
            errors.append('输入路径不能为空，且必须是已存在的文件夹或图片。')
        if not params['output_path']:
            errors.append('输出路径不能为空。')
        try:
            size = int(params['size'])
            if size <= 0 or size % 32 != 0:
                errors.append('图片尺寸必须为正数且为32的倍数。')
        except Exception:
            errors.append('图片尺寸必须为整数。')
        try:
            sigma = float(params['denoiser_sigma'])
            if sigma < 0:
                errors.append('去噪sigma不能为负数。')
        except Exception:
            errors.append('去噪sigma必须为数字。')
        if errors:
            messagebox.showerror('参数错误', '\n'.join(errors))
            return
        # 参数确认弹窗
        confirm_msg = f"请确认以下参数：\n输入路径: {params['input_path']}\n输出路径: {params['output_path']}\n图片尺寸: {params['size']}\n去噪: {params['denoiser']}\n去噪sigma: {params['denoiser_sigma']}\n色相/饱和度微调: {params['hue_sat_adjust']}\n生成器: {params['generator']}\n特征提取器: {params['extractor']}\nNVIDIA GPU: {params['gpu']}\nApple M1/M2加速: {params['mps']}"
        if not messagebox.askokcancel('参数确认', confirm_msg):
            return
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, '任务启动...\n')
        self.log_text.config(state='disabled')
        def run():
            try:
                cmd = [
                    'python', 'inference.py',
                    '-p', params['input_path'],
                    '-sd', params['output_path']
                ]
                # keep_ratio: 若为True则加--keep_ratio，否则加-s
                if params.get('keep_ratio', False):
                    cmd.append('--keep_ratio')
                else:
                    cmd += ['-s', str(params['size'])]
                if not params['denoiser']:
                    cmd.append('--no_denoise')
                else:
                    cmd += ['-ds', str(params['denoiser_sigma'])]
                if not params['hue_sat_adjust']:
                    cmd.append('--no_hue_sat_adjust')
                if params['generator'] != 'networks/generator.zip':
                    cmd += ['-gen', params['generator']]
                if params['extractor'] != 'networks/extractor.pth':
                    cmd += ['-ext', params['extractor']]
                if params['gpu']:
                    cmd.append('-g')
                if params.get('dpi', 300):
                    cmd += ['--dpi', str(params['dpi'])]
                if params.get('hue_shift', 0.02) != 0.02:
                    cmd += ['--hue_shift', str(params['hue_shift'])]
                if params.get('sat_shift', -0.10) != -0.10:
                    cmd += ['--sat_shift', str(params['sat_shift'])]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
                self.subprocesses.append(process)
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        self.log_text.config(state='normal')
                        self.log_text.insert(tk.END, line)
                        self.log_text.see(tk.END)
                        self.log_text.update_idletasks()
                        self.log_text.config(state='disabled')
                process.stdout.close()
                code = process.wait()
                if code != 0:
                    messagebox.showerror('运行出错', '批量处理过程中发生错误，请检查参数设置或日志内容，修正后重试。')
            except Exception as e:
                messagebox.showerror('运行异常', f'批量处理启动失败：{e}\n请检查参数设置和环境，修正后重试。')
        threading.Thread(target=run, daemon=True).start()

    def run_single(self):
        params = self.get_single_params_from_ui()
        errors = []
        if not params['input_path'] or not os.path.isfile(params['input_path']):
            errors.append('输入图像不能为空，且必须是已存在的图片文件。')
        if not params['output_path']:
            errors.append('输出路径不能为空。')
        try:
            size = int(params['size'])
            if size <= 0 or size % 32 != 0:
                errors.append('图片尺寸必须为正数且为32的倍数。')
        except Exception:
            errors.append('图片尺寸必须为整数。')
        try:
            sigma = float(params['denoiser_sigma'])
            if sigma < 0:
                errors.append('去噪sigma不能为负数。')
        except Exception:
            errors.append('去噪sigma必须为数字。')
        if errors:
            messagebox.showerror('参数错误', '\n'.join(errors))
            return
        # 参数确认弹窗
        confirm_msg = f"请确认以下参数：\n输入图像: {params['input_path']}\n输出路径: {params['output_path']}\n图片尺寸: {params['size']}\n去噪: {params['denoiser']}\n去噪sigma: {params['denoiser_sigma']}\n色相/饱和度微调: {params['hue_sat_adjust']}\n生成器: {params['generator']}\n特征提取器: {params['extractor']}\nNVIDIA GPU: {params['gpu']}\nApple M1/M2加速: {params['mps']}"
        if not messagebox.askokcancel('参数确认', confirm_msg):
            return
        self.single_log_text.config(state='normal')
        self.single_log_text.delete(1.0, tk.END)
        self.single_log_text.insert(tk.END, '任务启动...\n')
        self.single_log_text.config(state='disabled')
        def run():
            temp_dir = None
            try:
                temp_dir = tempfile.mkdtemp(prefix='singleimg_')
                img_name = os.path.basename(params['input_path'])
                temp_img_path = os.path.join(temp_dir, img_name)
                shutil.copy2(params['input_path'], temp_img_path)
                cmd = [
                    'python', 'inference.py',
                    '-p', temp_dir,
                    '-sd', params['output_path'],
                    '-s', str(params['size'])
                ]
                if not params['denoiser']:
                    cmd.append('--no_denoise')
                else:
                    cmd += ['-ds', str(params['denoiser_sigma'])]
                if not params['hue_sat_adjust']:
                    cmd.append('--no_hue_sat_adjust')
                if params['generator'] != 'networks/generator.zip':
                    cmd += ['-gen', params['generator']]
                if params['extractor'] != 'networks/extractor.pth':
                    cmd += ['-ext', params['extractor']]
                if params['gpu']:
                    cmd.append('-g')
                if params.get('dpi', 300):
                    cmd += ['--dpi', str(params['dpi'])]
                if params.get('hue_shift', 0.02) != 0.02:
                    cmd += ['--hue_shift', str(params['hue_shift'])]
                if params.get('sat_shift', -0.10) != -0.10:
                    cmd += ['--sat_shift', str(params['sat_shift'])]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
                self.subprocesses.append(process)
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        self.single_log_text.config(state='normal')
                        self.single_log_text.insert(tk.END, line)
                        self.single_log_text.see(tk.END)
                        self.single_log_text.update_idletasks()
                        self.single_log_text.config(state='disabled')
                process.stdout.close()
                code = process.wait()
                if code != 0:
                    messagebox.showerror('运行出错', '处理图像过程中发生错误，请检查参数设置或日志内容，修正后重试。')
            except Exception as e:
                messagebox.showerror('运行异常', f'处理图像启动失败：{e}\n请检查参数设置和环境，修正后重试。')
            finally:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        threading.Thread(target=run, daemon=True).start()

    def stop_batch(self):
        # 终止所有子进程
        stopped = False
        for p in self.subprocesses:
            try:
                if p.poll() is None:
                    p.terminate()
                    stopped = True
            except Exception:
                pass
        if stopped:
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, '\n任务已被用户终止。\n')
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        else:
            messagebox.showinfo('提示', '当前没有正在运行的任务。')

if __name__ == '__main__':
    root = tk.Tk()
    app = MangaColorGUI(root)
    root.mainloop()
