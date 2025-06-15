import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import json
import tempfile
import shutil
import fnmatch
import codecs

class TextReplaceTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Adrts超级文本替换工具")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 设置统一的中文字体
        self.font = ('SimHei', 10)
        self.title_font = ('SimHei', 11, 'bold')  # 标题字体
        
        # 临时文件夹
        self.temp_dir = tempfile.mkdtemp()
        
        # 数据存储
        self.replace_rules = []  # 存储替换规则
        self.file_list = []  # 存储待处理的文件列表
        self.failed_files = []  # 存储替换失败的文件及原因
        
        # 可用的编码器列表
        self.available_encodings = [
            'utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1', 'ascii',
            'iso-8859-1', 'iso-8859-2', 'iso-8859-3', 'iso-8859-4',
            'iso-8859-5', 'iso-8859-6', 'iso-8859-7', 'iso-8859-8',
            'iso-8859-9', 'iso-8859-10', 'iso-8859-11', 'iso-8859-13',
            'iso-8859-14', 'iso-8859-15', 'iso-8859-16',
            'windows-1250', 'windows-1251', 'windows-1252', 'windows-1253',
            'windows-1254', 'windows-1255', 'windows-1256', 'windows-1257',
            'windows-1258'
        ]
        
        # 创建UI
        self.create_ui()
        
        # 程序关闭时清理临时文件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_ui(self):
        # 创建自定义样式
        style = ttk.Style()
        style.configure("Custom.TLabelframe.Label", font=self.title_font)
        
        # 主框架 - 使用网格布局
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # 设置行列权重，使界面可伸缩
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)  # 内容区域可伸缩
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 顶部文件选择区 - 使用LabelFrame
        file_frame = ttk.LabelFrame(
            main_frame, 
            text="文件选择", 
            style="Custom.TLabelframe", 
            padding=5,
            relief="groove"
        )
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 文件选择模式
        mode_frame = ttk.Frame(file_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.file_mode = tk.StringVar(value="single")
        
        ttk.Radiobutton(mode_frame, text="单个文件", variable=self.file_mode, value="single", 
                        command=self.update_file_controls).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(mode_frame, text="多个文件", variable=self.file_mode, value="multiple", 
                        command=self.update_file_controls).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(mode_frame, text="目录", variable=self.file_mode, value="directory", 
                        command=self.update_file_controls).pack(side=tk.LEFT)
        
        # 文件路径选择
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(path_frame, text="文件/目录路径:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.path_entry = ttk.Entry(path_frame, font=self.font)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(path_frame, text="浏览...", command=self.browse_files)
        browse_btn.pack(side=tk.LEFT)
        
        # 目录选项
        self.dir_options_frame = ttk.Frame(file_frame)
        
        # 使用网格布局优化目录选项区域
        self.dir_options_frame.columnconfigure(0, weight=1)
        self.dir_options_frame.columnconfigure(1, weight=1)
        
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.dir_options_frame, text="递归子文件夹", variable=self.recursive_var).grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
        
        filter_frame = ttk.Frame(self.dir_options_frame)
        filter_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Label(filter_frame, text="文件过滤:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar(value="*.*")
        ttk.Entry(filter_frame, textvariable=self.filter_var, width=20, font=self.font).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 编码选项
        encoding_frame = ttk.Frame(file_frame)
        encoding_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(encoding_frame, text="读取编码:").pack(side=tk.LEFT, padx=(0, 5))
        self.read_encoding = tk.StringVar(value="try-all")
        ttk.Combobox(encoding_frame, textvariable=self.read_encoding, 
                    values=["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1", "ascii", "auto-detect", "try-all"],
                    width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(encoding_frame, text="写入编码:").pack(side=tk.LEFT, padx=(0, 5))
        self.write_encoding = tk.StringVar(value="utf-8")
        ttk.Combobox(encoding_frame, textvariable=self.write_encoding, 
                    values=["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1", "ascii"],
                    width=15).pack(side=tk.LEFT)
        
        # 中部内容区
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=2, column=0, sticky=(tk.N, tk.S, tk.W, tk.E), pady=(0, 10))
        
        # 设置内容区域的行列权重
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # 使用PanedWindow分隔规则区域和日志区域，允许用户调整比例
        paned_window = ttk.PanedWindow(content_frame, orient=tk.VERTICAL)
        paned_window.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # 规则表格和按钮 - 使用LabelFrame
        rules_frame = ttk.LabelFrame(
            paned_window, 
            text="替换规则", 
            style="Custom.TLabelframe", 
            padding=5,
            relief="groove"
        )
        paned_window.add(rules_frame, weight=1)
        
        # 使用网格布局优化规则区域
        rules_frame.grid_rowconfigure(0, weight=1)
        rules_frame.grid_columnconfigure(0, weight=1)
        
        # 创建Treeview表格
        columns = ("alias", "find", "replace", "regex")
        self.rules_tree = ttk.Treeview(rules_frame, columns=columns, show="headings", height=8)
        self.rules_tree.heading("alias", text="规则别名")
        self.rules_tree.heading("find", text="查找内容")
        self.rules_tree.heading("replace", text="替换内容")
        self.rules_tree.heading("regex", text="正则")
        
        self.rules_tree.column("alias", width=120)
        self.rules_tree.column("find", width=180)
        self.rules_tree.column("replace", width=180)
        self.rules_tree.column("regex", width=60, anchor=tk.CENTER)
        
        self.rules_tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(rules_frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.rules_tree.configure(yscroll=tree_scroll.set)
        
        # 右侧规则操作按钮 - 使用网格布局
        btn_frame = ttk.Frame(rules_frame)
        btn_frame.grid(row=0, column=2, sticky=(tk.N, tk.W), padx=(10, 0))
        
        btn_width = 12
        ttk.Button(btn_frame, text="添加规则", width=btn_width, command=self.add_rule).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Button(btn_frame, text="编辑规则", width=btn_width, command=self.edit_rule).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Button(btn_frame, text="删除规则", width=btn_width, command=self.delete_rule).grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Button(btn_frame, text="清空规则", width=btn_width, command=self.clear_rules).grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Button(btn_frame, text="保存规则", width=btn_width, command=self.save_rules).grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Button(btn_frame, text="加载规则", width=btn_width, command=self.load_rules).grid(row=5, column=0, sticky=tk.W)
        
        # 消息日志区域
        log_frame = ttk.LabelFrame(
            paned_window, 
            text="消息日志", 
            style="Custom.TLabelframe", 
            padding=5,
            relief="groove"
        )
        paned_window.add(log_frame, weight=1)
        
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        # 使用与替换规则相同的字体设置
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=self.font, height=8)
        self.log_text.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # 底部控制区 - 使用网格布局
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        bottom_frame.grid_columnconfigure(0, weight=1)
        
        # 左侧临时文件提示
        temp_frame = ttk.Frame(bottom_frame)
        temp_frame.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(temp_frame, text=f"临时文件位置: {self.temp_dir}").pack(anchor=tk.W)
        
        # 右侧按钮
        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.grid(row=0, column=1, sticky=tk.E)
        
        self.execute_btn = ttk.Button(btn_frame, text="执行替换", command=self.execute_replace)
        self.execute_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = ttk.Button(btn_frame, text="清空消息", command=self.clear_log)
        clear_btn.pack(side=tk.LEFT)
        
        # 状态栏
        self.status_bar = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 初始化文件控件状态
        self.update_file_controls()
    
    def update_file_controls(self):
        """根据文件选择模式更新控件状态"""
        mode = self.file_mode.get()
        
        # 重置目录选项框架
        if hasattr(self, 'dir_options_frame') and self.dir_options_frame.winfo_ismapped():
            self.dir_options_frame.pack_forget()
        
        # 根据模式启用/禁用控件
        if mode == "directory":
            self.dir_options_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.path_entry.delete(0, tk.END)
    
    def browse_files(self):
        """浏览并选择文件或目录"""
        mode = self.file_mode.get()
        self.path_entry.delete(0, tk.END)
        
        if mode == "single":
            filename = filedialog.askopenfilename(title="选择单个文件")
            if filename:
                self.path_entry.insert(0, filename)
                
        elif mode == "multiple":
            filenames = filedialog.askopenfilenames(title="选择多个文件")
            if filenames:
                self.path_entry.insert(0, ", ".join(filenames))
                
        elif mode == "directory":
            directory = filedialog.askdirectory(title="选择目录")
            if directory:
                self.path_entry.insert(0, directory)
    
    def update_file_list(self):
        """根据选择更新文件列表"""
        self.file_list = []
        mode = self.file_mode.get()
        path = self.path_entry.get().strip()
        
        if not path:
            return
            
        try:
            if mode == "single":
                if os.path.isfile(path):
                    self.file_list = [path]
                    self.log(f"已选择文件: {path}")
                else:
                    self.log(f"错误: 文件不存在 - {path}")
                    
            elif mode == "multiple":
                file_paths = [p.strip() for p in path.split(",") if p.strip()]
                valid_files = []
                
                for file_path in file_paths:
                    if os.path.isfile(file_path):
                        valid_files.append(file_path)
                    else:
                        self.log(f"警告: 文件不存在 - {file_path}")
                
                self.file_list = valid_files
                self.log(f"已选择 {len(valid_files)} 个文件")
                
            elif mode == "directory":
                if os.path.isdir(path):
                    filter_text = self.filter_var.get()
                    filter_patterns = [p.strip() for p in filter_text.split(',') if p.strip()]
                    
                    if not filter_patterns:
                        filter_patterns = ["*.*"]  # 默认匹配所有文件
                    
                    self.log(f"扫描目录: {path}，过滤模式: {filter_text}")
                    
                    # 编译所有过滤模式的正则表达式
                    regex_patterns = [re.compile(fnmatch.translate(pattern), re.IGNORECASE) 
                                     for pattern in filter_patterns]
                    
                    # 获取文件列表
                    file_list = []
                    
                    if self.recursive_var.get():
                        for root, _, files in os.walk(path):
                            for file in files:
                                # 检查文件是否匹配任何一个过滤模式
                                for pattern in regex_patterns:
                                    if pattern.match(file):
                                        file_list.append(os.path.join(root, file))
                                        break
                    else:
                        for file in os.listdir(path):
                            file_path = os.path.join(path, file)
                            if os.path.isfile(file_path):
                                # 检查文件是否匹配任何一个过滤模式
                                for pattern in regex_patterns:
                                    if pattern.match(file):
                                        file_list.append(file_path)
                                        break
                    
                    self.file_list = file_list
                    self.log(f"找到 {len(file_list)} 个匹配的文件")
                else:
                    self.log(f"错误: 目录不存在 - {path}")
                    
        except Exception as e:
            self.log(f"错误: 更新文件列表时出错 - {str(e)}")
    
    def clear_log(self):
        """清空日志消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def add_rule(self):
        """添加新的替换规则"""
        dialog = RuleDialog(self.root, self, "添加规则")
        self.root.wait_window(dialog.top)  # 等待对话框关闭
        self.refresh_rules_tree()  # 刷新规则表格
    
    def edit_rule(self):
        """编辑选中的替换规则"""
        selected_item = self.rules_tree.selection()
        if not selected_item:
            self.log("请先选择要编辑的规则")
            return
            
        index = self.rules_tree.index(selected_item[0])
        dialog = RuleDialog(self.root, self, "编辑规则", index)
        self.root.wait_window(dialog.top)  # 等待对话框关闭
        self.refresh_rules_tree()  # 刷新规则表格
    
    def delete_rule(self):
        """删除选中的替换规则"""
        selected_item = self.rules_tree.selection()
        if not selected_item:
            self.log("请先选择要删除的规则")
            return
            
        if messagebox.askyesno("确认删除", "确定要删除选中的规则吗?"):
            index = self.rules_tree.index(selected_item[0])
            del self.replace_rules[index]
            self.refresh_rules_tree()
            self.log(f"已删除规则: {index+1}")
    
    def clear_rules(self):
        """清空所有替换规则"""
        if not self.replace_rules:
            return
            
        if messagebox.askyesno("确认清空", "确定要清空所有规则吗?"):
            self.replace_rules = []
            self.refresh_rules_tree()
            self.log("已清空所有规则")
    
    def save_rules(self):
        """保存替换规则到文件"""
        if not self.replace_rules:
            self.log("没有规则可保存")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="保存规则"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.replace_rules, f, ensure_ascii=False, indent=4)
                self.log(f"规则已保存到: {filename}")
            except Exception as e:
                self.log(f"错误: 保存规则时出错 - {str(e)}")
    
    def load_rules(self):
        """从文件加载替换规则"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="加载规则"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.replace_rules = json.load(f)
                self.refresh_rules_tree()
                self.log(f"已从 {filename} 加载 {len(self.replace_rules)} 条规则")
            except Exception as e:
                self.log(f"错误: 加载规则时出错 - {str(e)}")
    
    def refresh_rules_tree(self):
        """刷新规则表格显示"""
        # 清空现有项
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # 添加规则
        for rule in self.replace_rules:
            # 在表格中显示✓或✗表示是否启用正则
            regex_mark = "✓" if rule.get("regex", False) else "✗"
            self.rules_tree.insert("", tk.END, values=(
                rule["alias"], 
                rule["find"], 
                rule["replace"],
                regex_mark
            ))
    
    def log(self, message):
        """添加日志消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def execute_replace(self):
        """执行替换操作"""
        # 重置失败文件列表
        self.failed_files = []
        
        # 在替换前更新文件列表
        self.update_file_list()
        
        if not self.file_list:
            self.log("错误: 没有选择要处理的文件")
            return
            
        if not self.replace_rules:
            self.log("错误: 没有定义替换规则")
            return
            
        # 更新状态栏
        self.status_bar.config(text="正在处理文件...")
        self.progress["value"] = 0
        self.root.update()
        
        total_files = len(self.file_list)
        success_count = 0
        failed_count = 0
        
        for i, file_path in enumerate(self.file_list):
            try:
                self.log(f"\n处理文件: {file_path}")
                self.process_file(file_path)
                success_count += 1
            except Exception as e:
                error_msg = str(e)
                self.log(f"错误: 处理文件时出错 - {error_msg}")
                self.failed_files.append((file_path, error_msg))
                failed_count += 1
            
            # 更新进度条
            self.progress["value"] = (i + 1) / total_files * 100
            self.root.update()
        
        # 更新状态栏
        self.status_bar.config(text=f"处理完成: 成功 {success_count} 个，失败 {failed_count} 个")
        
        # 显示失败文件列表
        if self.failed_files:
            self.log("\n========== 替换失败的文件 ==========")
            for file_path, error_msg in self.failed_files:
                self.log(f"文件: {file_path}")
                self.log(f"错误: {error_msg}")
                self.log("-------------------------------")
        
        # 显示结果消息
        messagebox.showinfo("处理完成", 
                           f"处理完成!\n成功: {success_count} 个\n失败: {failed_count} 个")
    
    def detect_encoding(self, file_path):
        """检测文件编码"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(4)
        
        # 检查BOM
        if raw_data.startswith(codecs.BOM_UTF8):
            return 'utf-8-sig'
        elif raw_data.startswith(codecs.BOM_UTF16_LE):
            return 'utf-16-le'
        elif raw_data.startswith(codecs.BOM_UTF16_BE):
            return 'utf-16-be'
        elif raw_data.startswith(codecs.BOM_UTF32_LE):
            return 'utf-32-le'
        elif raw_data.startswith(codecs.BOM_UTF32_BE):
            return 'utf-32-be'
        
        # 默认返回utf-8
        return 'utf-8'
    
    def try_all_encodings(self, file_path):
        """尝试所有可用的编码器读取文件"""
        self.log("尝试所有可用的编码器读取文件...")
        
        for encoding in self.available_encodings:
            try:
                self.log(f"尝试编码: {encoding}")
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                self.log(f"成功使用 {encoding} 编码读取文件")
                return (content, encoding)
            except UnicodeDecodeError:
                continue
        
        # 如果所有编码器都失败
        raise Exception("无法使用任何可用的编码器读取文件")
    
    def process_file(self, file_path):
        """处理单个文件"""
        read_encoding = self.read_encoding.get()
        
        # 自动检测编码
        if read_encoding == "auto-detect":
            detected_encoding = self.detect_encoding(file_path)
            self.log(f"自动检测编码: {detected_encoding}")
            read_encoding = detected_encoding
        # 尝试所有编码器
        elif read_encoding == "try-all":
            content, used_encoding = self.try_all_encodings(file_path)
            read_encoding = used_encoding
        else:
            # 使用指定编码
            pass
        
        try:
            # 如果不是尝试所有编码器模式，则正常读取文件
            if read_encoding != "try-all":
                with open(file_path, 'r', encoding=read_encoding) as f:
                    content = f.read()
            
            original_content = content
            modified = False
            replacements = 0
            
            # 应用所有替换规则
            for rule in self.replace_rules:
                find_text = rule["find"]
                replace_text = rule["replace"]
                use_regex = rule.get("regex", False)
                
                if use_regex:
                    try:
                        # 使用正则表达式替换
                        pattern = re.compile(find_text, re.DOTALL)
                        new_content, count = pattern.subn(replace_text, content)
                        
                        if count > 0:
                            content = new_content
                            modified = True
                            replacements += count
                            self.log(f"应用正则规则: {rule['alias']} (替换 {count} 处)")
                    except re.error as e:
                        self.log(f"警告: 正则表达式错误 - {rule['alias']}: {str(e)}")
                else:
                    # 使用普通字符串替换
                    if find_text in content:
                        content = content.replace(find_text, replace_text)
                        modified = True
                        count = content.count(replace_text)
                        replacements += count
                        self.log(f"应用规则: {rule['alias']} (替换 {count} 处)")
            
            # 如果内容被修改，则保存
            if modified:
                self.log(f"共执行 {replacements} 处替换")
                
                # 创建临时文件
                temp_file = os.path.join(self.temp_dir, os.path.basename(file_path))
                
                # 写入修改后的内容
                with open(temp_file, 'w', encoding=self.write_encoding.get()) as f:
                    f.write(content)
                
                # 替换原文件
                shutil.copy2(temp_file, file_path)
                self.log(f"已保存修改到: {file_path}")
            else:
                self.log("没有需要替换的内容")
                
        except UnicodeDecodeError as e:
            # 记录编码错误
            error_msg = f"编码错误: 文件 {file_path} 无法使用 {read_encoding} 编码读取 - {str(e)}"
            self.log(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            # 记录其他错误
            error_msg = f"处理文件 {file_path} 时出错 - {str(e)}"
            self.log(error_msg)
            raise
    
    def on_closing(self):
        """程序关闭时清理资源"""
        if messagebox.askokcancel("退出", "确定要退出程序吗?"):
            # 清理临时文件
            try:
                if os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
                    self.log(f"已清理临时文件: {self.temp_dir}")
            except Exception as e:
                self.log(f"警告: 清理临时文件时出错 - {str(e)}")
            
            self.root.destroy()

class RuleDialog:
    """替换规则对话框"""
    def __init__(self, parent, app, title, rule_index=None):
        self.app = app
        self.rule_index = rule_index
        
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("500x450")  # 增加高度以容纳正则选项
        self.top.resizable(True, True)
        self.top.transient(parent)
        self.top.grab_set()
        
        # 设置中文字体
        self.font = ('SimHei', 10)
        
        # 创建UI
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 规则别名
        ttk.Label(main_frame, text="规则别名:", font=self.font).pack(anchor=tk.W, pady=(0, 5))
        self.alias_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.alias_var, font=self.font).pack(fill=tk.X, pady=(0, 10))
        
        # 查找内容
        ttk.Label(main_frame, text="查找内容:", font=self.font).pack(anchor=tk.W, pady=(0, 5))
        self.find_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.find_var, font=self.font).pack(fill=tk.X, pady=(0, 10))
        
        # 替换内容
        ttk.Label(main_frame, text="替换内容:", font=self.font).pack(anchor=tk.W, pady=(0, 5))
        self.replace_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10, font=self.font)
        self.replace_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 正则表达式选项
        regex_frame = ttk.Frame(main_frame)
        regex_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.regex_var = tk.BooleanVar()
        ttk.Checkbutton(regex_frame, text="使用正则表达式", variable=self.regex_var).pack(anchor=tk.W)
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="确定", command=self.on_ok).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="取消", command=self.top.destroy).pack(side=tk.LEFT)
        
        # 如果是编辑模式，加载现有规则
        if rule_index is not None and 0 <= rule_index < len(app.replace_rules):
            rule = app.replace_rules[rule_index]
            self.alias_var.set(rule["alias"])
            self.find_var.set(rule["find"])
            self.replace_text.delete(1.0, tk.END)
            self.replace_text.insert(tk.END, rule["replace"])
            self.regex_var.set(rule.get("regex", False))
    
    def on_ok(self):
        """确定按钮处理"""
        alias = self.alias_var.get().strip()
        find_text = self.find_var.get()
        replace_text = self.replace_text.get(1.0, tk.END).rstrip()
        use_regex = self.regex_var.get()
        
        if not alias:
            messagebox.showerror("错误", "规则别名不能为空")
            return
            
        if not find_text:
            messagebox.showerror("错误", "查找内容不能为空")
            return
            
        rule = {
            "alias": alias,
            "find": find_text,
            "replace": replace_text,
            "regex": use_regex
        }
        
        # 添加或更新规则
        if self.rule_index is not None and 0 <= self.rule_index < len(self.app.replace_rules):
            self.app.replace_rules[self.rule_index] = rule
            self.app.log(f"已更新规则: {alias}")
        else:
            self.app.replace_rules.append(rule)
            self.app.log(f"已添加规则: {alias}")
        
        # 关闭对话框
        self.top.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TextReplaceTool(root)
    root.mainloop()
### 主要改进点：
