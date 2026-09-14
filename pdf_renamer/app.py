import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import re
import datetime
import traceback

# 导入第三方库
try:
    import pypdf
    import pdfplumber
    import requests
except ImportError as e:
    messagebox.showerror("错误", f"缺少必要的依赖库: {e}\n请运行 pip install -r requirements.txt 安装。")
    sys.exit(1)

class PDFRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF文献重命名工具")
        self.root.geometry("1000x700")

        # 变量绑定
        self.folder_path = tk.StringVar()
        self.include_subfolders = tk.BooleanVar(value=False)
        self.use_crossref = tk.BooleanVar(value=False)

        # 保存扫描到的文件信息 [{'original_path': str, 'original_name': str, 'title': str, 'new_name': str, 'status': str, 'item_id': str}]
        self.file_data = []

        # 线程控制
        self.running = False

        self.setup_ui()

    def setup_ui(self):
        # 顶部控制区
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="选择文件夹", command=self.select_folder).grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(top_frame, textvariable=self.folder_path, width=70, state='readonly').grid(row=0, column=1, padx=5, pady=5, sticky='we')

        ttk.Checkbutton(top_frame, text="包含子文件夹", variable=self.include_subfolders).grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(top_frame, text="使用 DOI/Crossref 联网识别标题", variable=self.use_crossref).grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=2)

        btn_frame = ttk.Frame(top_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky='w', pady=10)

        self.btn_preview = ttk.Button(btn_frame, text="扫描预览", command=self.start_scan_preview)
        self.btn_preview.pack(side=tk.LEFT, padx=5)

        self.btn_rename = ttk.Button(btn_frame, text="执行重命名", command=self.start_execute_rename)
        self.btn_rename.pack(side=tk.LEFT, padx=5)

        self.btn_undo = ttk.Button(btn_frame, text="撤销上次重命名", command=self.start_undo_rename)
        self.btn_undo.pack(side=tk.LEFT, padx=5)

        # 中部表格区
        mid_frame = ttk.Frame(self.root, padding=10)
        mid_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("original_name", "title", "new_name", "status")
        self.tree = ttk.Treeview(mid_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("original_name", text="原文件名")
        self.tree.heading("title", text="识别标题")
        self.tree.heading("new_name", text="新文件名 (双击修改)")
        self.tree.heading("status", text="状态")

        self.tree.column("original_name", width=200)
        self.tree.column("title", width=300)
        self.tree.column("new_name", width=250)
        self.tree.column("status", width=150)

        vsb = ttk.Scrollbar(mid_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(mid_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        mid_frame.grid_columnconfigure(0, weight=1)
        mid_frame.grid_rowconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_double_click)

        # 底部进度条和日志区
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X)

        self.progress = ttk.Progressbar(bottom_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 5))

        self.log_text = tk.Text(bottom_frame, height=8, state='disabled')
        self.log_text.pack(fill=tk.X)
        self.log("程序启动。请先选择包含 PDF 的文件夹，然后点击“扫描预览”。")

    def log(self, message):
        self.root.after(0, self._log_ui, message)

    def _log_ui(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{datetime.datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def set_progress(self, value, maximum=100):
        self.root.after(0, self._set_progress_ui, value, maximum)

    def _set_progress_ui(self, value, maximum):
        self.progress['maximum'] = maximum
        self.progress['value'] = value

    def set_buttons_state(self, state):
        self.btn_preview.config(state=state)
        self.btn_rename.config(state=state)
        self.btn_undo.config(state=state)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.log(f"已选择文件夹: {folder}")

    def on_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)
        if column == '#3': # new_name 列
            item_id = self.tree.focus()
            if not item_id:
                return
            x, y, width, height = self.tree.bbox(item_id, column)

            value = self.tree.set(item_id, column)

            entry = ttk.Entry(self.tree)
            entry.place(x=x, y=y, width=width, height=height)
            entry.insert(0, value)
            entry.select_range(0, tk.END)
            entry.focus()

            def save_edit(event_or_none=None):
                try:
                    new_value = entry.get().strip()
                    if new_value and new_value.lower().endswith(".pdf"):
                        self.tree.set(item_id, column, new_value)
                        for data in self.file_data:
                            if data['item_id'] == item_id:
                                data['new_name'] = new_value
                                break
                        self.log(f"手动修改新文件名为: {new_value}")
                    else:
                        messagebox.showwarning("警告", "新文件名不能为空且必须以 .pdf 结尾")
                finally:
                    entry.destroy()

            entry.bind("<Return>", save_edit)
            entry.bind("<FocusOut>", save_edit)

    def extract_title(self, filepath):
        title = None
        # 1. 优先读取 PDF 元数据 Title
        try:
            with open(filepath, 'rb') as f:
                reader = pypdf.PdfReader(f)
                info = reader.metadata
                if info and info.title:
                    raw_title = info.title.strip()
                    # 规则：若为空、无效、像文件名、像“Microsoft Word - xxx”、长度小于 8 个字符，则忽略。
                    if len(raw_title) >= 8 and \
                       not raw_title.lower().endswith('.pdf') and \
                       not raw_title.startswith('Microsoft Word - ') and \
                       not raw_title.startswith('Untitled'):
                        return raw_title, "元数据提取"
        except Exception as e:
            pass # 忽略错误，继续下一种方法

        # 2. 其次用 pdfplumber 读取第一页文字，提取每行文字和字号
        try:
            with pdfplumber.open(filepath) as pdf:
                if pdf.pages:
                    first_page = pdf.pages[0]
                    words = first_page.extract_words(extra_attrs=["size"])

                    # 按字号分组并连接同行文字
                    lines = {}
                    for word in words:
                        # 用 y0 的近似值作为行的标识
                        y_rounded = round(word['top'], 1)
                        if y_rounded not in lines:
                            lines[y_rounded] = {'text': '', 'max_size': 0}
                        lines[y_rounded]['text'] += word['text'] + ' '
                        lines[y_rounded]['max_size'] = max(lines[y_rounded]['max_size'], word['size'])

                    # 过滤并找最大字号的连续文本行
                    best_line = ""
                    max_size_found = 0

                    # 简单过滤页眉、期刊名等 (通常在页面最顶端且字号较小，或者包含特定关键字)
                    # 真实世界中提取标题非常复杂，这里采用取第一页最大字号的启发式方法
                    for y, line_info in lines.items():
                        text = line_info['text'].strip()
                        size = line_info['max_size']

                        # 过滤太短的、像页码的
                        if len(text) < 5 or text.isdigit():
                            continue

                        # 如果字号更大，则更新
                        if size > max_size_found:
                            max_size_found = size
                            best_line = text
                        elif size == max_size_found and best_line:
                            # 假设是多行标题
                            best_line += " " + text

                    if best_line and len(best_line) >= 8:
                        # 在尝试 DOI 之前，先看看是否有好的文本
                        title = best_line
        except Exception as e:
            pass

        # 3. 如果勾选“使用 DOI/Crossref 联网识别标题”，则提取 DOI
        if self.use_crossref.get():
            try:
                text = ""
                with pdfplumber.open(filepath) as pdf:
                    if pdf.pages:
                        text = pdf.pages[0].extract_text() or ""

                # 正则匹配 DOI (简化的匹配模式)
                doi_match = re.search(r'\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b', text, re.IGNORECASE)
                if doi_match:
                    doi = doi_match.group(1)
                    # 调用 API
                    try:
                        url = f"https://api.crossref.org/works/{doi}"
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if 'message' in data and 'title' in data['message']:
                                api_titles = data['message']['title']
                                if api_titles and isinstance(api_titles, list):
                                    return api_titles[0], "Crossref DOI 识别"
                    except requests.exceptions.RequestException as e:
                        pass # 网络错误，忽略
            except Exception as e:
                pass

        if title:
            return title, "内容字号提取"

        # 4. 如果都失败
        return None, "无法识别，保留原名"

    # 以下是多线程包装方法
    def start_scan_preview(self):
        if not self.folder_path.get():
            messagebox.showwarning("警告", "请先选择文件夹")
            return
        self.set_buttons_state(tk.DISABLED)
        self.tree.delete(*self.tree.get_children())
        self.file_data.clear()
        threading.Thread(target=self.scan_preview_thread, daemon=True).start()

    def start_execute_rename(self):
        if not self.file_data:
            messagebox.showwarning("警告", "请先进行扫描预览，并确保有需要重命名的文件")
            return
        self.set_buttons_state(tk.DISABLED)
        threading.Thread(target=self.execute_rename_thread, daemon=True).start()

    def start_undo_rename(self):
        self.set_buttons_state(tk.DISABLED)
        threading.Thread(target=self.undo_rename_thread, daemon=True).start()

    def sanitize_filename(self, title):
        # 1. 去掉非法字符
        title = re.sub(r'[\\/:*?"<>|]', '', title)
        # 2. 去掉控制字符 0-31
        title = "".join(ch for ch in title if ord(ch) > 31)
        # 3. 去掉开头和结尾的空格、点号
        title = title.strip(' .')

        # 4. Windows 保留名处理
        reserved_names = {"CON", "PRN", "AUX", "NUL",
                          "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
                          "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
        if title.upper() in reserved_names:
            title += "_"

        # 5. 长度限制 (标题部分最长 100 个字符)
        if len(title) > 100:
            title = title[:100].strip(' .')

        return title

    def get_unique_filename(self, directory, new_name):
        base_name, ext = os.path.splitext(new_name)
        ext = ".pdf" # 强制要求 .pdf
        counter = 1
        final_name = new_name

        while os.path.exists(os.path.join(directory, final_name)):
            final_name = f"{base_name}({counter}){ext}"
            counter += 1

        return final_name

    def write_log_csv(self, log_entries):
        csv_path = os.path.join(self.folder_path.get(), "rename_log.csv")
        file_exists = os.path.exists(csv_path)
        try:
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["原路径", "新路径", "状态", "时间", "错误信息"])
                for entry in log_entries:
                    writer.writerow(entry)
        except Exception as e:
            self.log(f"无法写入日志文件 rename_log.csv: {e}")

    def scan_preview_thread(self):
        try:
            folder = self.folder_path.get()
            self.log(f"开始扫描目录: {folder}")

            pdf_files = []
            if self.include_subfolders.get():
                for root_dir, dirs, files in os.walk(folder):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_files.append(os.path.join(root_dir, file))
            else:
                for file in os.listdir(folder):
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(folder, file))

            total_files = len(pdf_files)
            if total_files == 0:
                self.log("未找到任何 PDF 文件")
                self.set_progress(100)
                return

            self.set_progress(0, total_files)

            for index, filepath in enumerate(pdf_files):
                filename = os.path.basename(filepath)

                title, status = self.extract_title(filepath)

                if title:
                    clean_title = self.sanitize_filename(title)
                    new_name = f"{clean_title}.pdf"
                else:
                    new_name = filename

                # 更新 UI
                def update_tree(fp, fn, t, nn, st):
                    item_id = self.tree.insert("", tk.END, values=(fn, t or "-", nn, st))
                    self.file_data.append({
                        'original_path': fp,
                        'original_name': fn,
                        'title': t,
                        'new_name': nn,
                        'status': st,
                        'item_id': item_id
                    })

                self.root.after(0, update_tree, filepath, filename, title, new_name, status)
                self.set_progress(index + 1, total_files)

            self.log(f"扫描预览完成，共发现 {total_files} 个 PDF 文件。")

        except Exception as e:
            self.log(f"扫描出错: {e}")
            traceback.print_exc()
        finally:
            self.root.after(0, lambda: self.set_buttons_state(tk.NORMAL))

    def execute_rename_thread(self):
        try:
            self.log("开始执行重命名...")
            total = len(self.file_data)
            self.set_progress(0, total)

            log_entries = []
            success_count = 0

            for index, data in enumerate(self.file_data):
                original_path = data['original_path']
                original_dir = os.path.dirname(original_path)
                new_name = data['new_name']
                item_id = data['item_id']

                if data['original_name'] == new_name:
                    self.set_progress(index + 1, total)
                    continue # 不需要重命名

                # 检查长度
                if len(os.path.join(original_dir, new_name)) > 240:
                    # 尝试进一步截断
                    base = os.path.splitext(new_name)[0]
                    base = base[:50].strip(' .')
                    new_name = f"{base}.pdf"
                    self.log(f"路径过长，进一步截断为: {new_name}")

                new_name = self.get_unique_filename(original_dir, new_name)
                new_path = os.path.join(original_dir, new_name)

                error_msg = ""
                status_msg = "重命名成功"
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                try:
                    # 尝试取消只读属性 (Windows)
                    try:
                        import stat
                        if not os.access(original_path, os.W_OK):
                            os.chmod(original_path, stat.S_IWRITE)
                    except Exception:
                        pass

                    os.rename(original_path, new_path)
                    success_count += 1

                    # 更新 Treeview 和数据
                    data['original_path'] = new_path
                    data['original_name'] = new_name
                    data['status'] = status_msg
                    self.root.after(0, lambda i_id=item_id, s=status_msg: self.tree.set(i_id, "status", s))

                except Exception as e:
                    status_msg = "失败"
                    error_msg = str(e)
                    self.log(f"重命名失败 {original_path} -> {new_path}: {e}")
                    self.root.after(0, lambda i_id=item_id, s="重命名失败": self.tree.set(i_id, "status", s))
                    new_path = original_path # 记录日志时新路径等于原路径，表示未修改

                log_entries.append([original_path, new_path, status_msg, now_str, error_msg])
                self.set_progress(index + 1, total)

            if log_entries:
                self.write_log_csv(log_entries)

            self.log(f"重命名完成，成功 {success_count}/{total} 个。")

        except Exception as e:
            self.log(f"重命名出错: {e}")
            traceback.print_exc()
        finally:
            self.root.after(0, lambda: self.set_buttons_state(tk.NORMAL))

    def undo_rename_thread(self):
        try:
            csv_path = os.path.join(self.folder_path.get(), "rename_log.csv")
            if not os.path.exists(csv_path):
                self.log("未找到 rename_log.csv，无法撤销。")
                return

            self.log("准备撤销上一次的批量重命名...")

            # 读取日志，按时间分组找出最后一次操作批次
            logs = []
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    for row in reader:
                        if len(row) >= 5:
                            logs.append(row)
            except Exception as e:
                self.log(f"读取日志失败: {e}")
                return

            if not logs:
                self.log("日志为空，无撤销记录。")
                return

            # 找到最近的一批记录 (以时间大致相同为准，或者找最近的且状态为成功的记录)
            logs.reverse()
            last_time = None
            to_undo = []

            for row in logs:
                orig_p, new_p, status, time_str, err = row
                if status == "重命名成功" and orig_p != new_p:
                    # 提取分钟级别作为批次
                    batch_time = time_str[:16]
                    if last_time is None:
                        last_time = batch_time
                        to_undo.append((orig_p, new_p))
                    elif batch_time == last_time:
                        to_undo.append((orig_p, new_p))
                    else:
                        break # 已跨越到上一次批次

            if not to_undo:
                self.log("找不到可撤销的成功记录。")
                return

            self.log(f"共发现 {len(to_undo)} 条可撤销记录，开始撤销...")
            self.set_progress(0, len(to_undo))

            success_count = 0
            new_logs = []
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for i, (orig_p, new_p) in enumerate(to_undo):
                if os.path.exists(new_p):
                    try:
                        os.rename(new_p, orig_p)
                        success_count += 1
                        new_logs.append([new_p, orig_p, "撤销成功", now_str, ""])
                        self.log(f"撤销: {os.path.basename(new_p)} -> {os.path.basename(orig_p)}")
                    except Exception as e:
                        self.log(f"撤销失败 {new_p}: {e}")
                        new_logs.append([new_p, orig_p, "撤销失败", now_str, str(e)])
                else:
                    self.log(f"撤销失败: 找不到文件 {new_p}")
                    new_logs.append([new_p, orig_p, "撤销失败(文件丢失)", now_str, "文件不存在"])

                self.set_progress(i + 1, len(to_undo))

            if new_logs:
                self.write_log_csv(new_logs)

            self.log(f"撤销完成，成功 {success_count}/{len(to_undo)} 个。建议重新扫描目录。")

        except Exception as e:
            self.log(f"撤销出错: {e}")
            traceback.print_exc()
        finally:
            self.root.after(0, lambda: self.set_buttons_state(tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFRenamerApp(root)
    root.mainloop()
