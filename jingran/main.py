import customtkinter
import json
import os
import datetime
import base64
import secrets
import string
import tkinter.messagebox
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class PasswordVault:
    def __init__(self, master_password):
        self.master_password = master_password
        self.vault_file = os.path.join(os.path.dirname(__file__), "vault.enc")
        self.salt = None
        self.key = None
        self.fernet = None
        self.passwords = []

    def _generate_key(self, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        return key

    def setup_new(self):
        self.salt = os.urandom(16)
        self.key = self._generate_key(self.salt)
        self.fernet = Fernet(self.key)
        self.passwords = []
        self.save()
        return True

    def load(self):
        if not os.path.exists(self.vault_file):
            return False

        with open(self.vault_file, 'rb') as f:
            file_data = f.read()

        try:
            # First 16 bytes is salt
            self.salt = file_data[:16]
            encrypted_data = file_data[16:]

            self.key = self._generate_key(self.salt)
            self.fernet = Fernet(self.key)

            decrypted_data = self.fernet.decrypt(encrypted_data)
            self.passwords = json.loads(decrypted_data.decode('utf-8'))
            return True
        except (InvalidToken, ValueError, Exception) as e:
            return False

    def save(self):
        if not self.fernet:
            return False

        json_data = json.dumps(self.passwords, ensure_ascii=False).encode('utf-8')
        encrypted_data = self.fernet.encrypt(json_data)

        with open(self.vault_file, 'wb') as f:
            f.write(self.salt + encrypted_data)
        return True

# 设置整体外观和颜色主题
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # 设置默认字体
        self.default_font = customtkinter.CTkFont(family="MiSans")
        self.strike_font = customtkinter.CTkFont(family="MiSans", overstrike=True)

        # 主窗口标题和大小设置
        self.title("井然 - 我的桌面管家")
        self.geometry("1000x650")
        self.resizable(False, False)

        # 整体配色使用深色背景
        self.configure(fg_color="#1e1e1e")

        # 将窗口居中显示
        self.center_window(1000, 650)

        # 定义网格布局: 1行, 2列
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ============ 左侧导航栏 ============
        # 导航栏容器，宽度设置为 200，并固定为深灰色
        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="#252526")
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1) # 第4行（底部按钮前）自动拉伸，让设置按钮沉底

        # 导航栏标题
        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text="  井 然", font=customtkinter.CTkFont(family="MiSans", size=24, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=(20, 40))

        # 待办事项按钮
        self.todo_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="待办事项",
                                                   font=self.default_font,
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   anchor="w", command=self.todo_button_event)
        self.todo_button.grid(row=1, column=0, sticky="ew")

        # 密码管理按钮
        self.password_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="密码管理",
                                                      font=self.default_font,
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      anchor="w", command=self.password_button_event)
        self.password_button.grid(row=2, column=0, sticky="ew")

        # 桌面整理按钮
        self.desktop_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="桌面整理",
                                                      font=self.default_font,
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      anchor="w", command=self.desktop_button_event)
        self.desktop_button.grid(row=3, column=0, sticky="ew")

        # 设置按钮 (固定在底部)
        self.settings_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="设置",
                                                       font=self.default_font,
                                                       fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                       anchor="w", command=self.settings_button_event)
        self.settings_button.grid(row=5, column=0, sticky="ew", pady=(0, 20))


        # ============ 右侧内容区 ============

        # 待办事项页面
        self.todo_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.todo_frame.grid_columnconfigure(0, weight=1)
        self.todo_frame.grid_rowconfigure(0, weight=0)
        self.todo_frame.grid_rowconfigure(1, weight=0)
        self.todo_frame.grid_rowconfigure(2, weight=1)

        # 待办事项: 顶部输入区
        self.todo_header = customtkinter.CTkFrame(self.todo_frame, fg_color="transparent")
        self.todo_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.todo_header.grid_columnconfigure(0, weight=1)

        self.task_entry = customtkinter.CTkEntry(self.todo_header, placeholder_text="添加新任务...", font=self.default_font, height=35)
        self.task_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.priority_option = customtkinter.CTkOptionMenu(self.todo_header, values=["普通", "重要", "紧急"], font=self.default_font, width=80)
        self.priority_option.grid(row=0, column=1, padx=(0, 10))

        # 截止时间下拉菜单组合
        self.deadline_frame = customtkinter.CTkFrame(self.todo_header, fg_color="transparent")
        self.deadline_frame.grid(row=0, column=2, padx=(0, 10))

        current_year = datetime.datetime.now().year
        years = [str(y) for y in range(current_year, current_year + 11)]
        months = [f"{m:02d}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]
        hours = [f"{h:02d}" for h in range(0, 24)]
        minutes = [f"{m:02d}" for m in range(0, 60)]

        self.year_option = customtkinter.CTkOptionMenu(self.deadline_frame, values=years, font=self.default_font, width=70)
        self.year_option.grid(row=0, column=0, padx=(0, 5))

        self.month_option = customtkinter.CTkOptionMenu(self.deadline_frame, values=months, font=self.default_font, width=60)
        self.month_option.grid(row=0, column=1, padx=(0, 5))

        self.day_option = customtkinter.CTkOptionMenu(self.deadline_frame, values=days, font=self.default_font, width=60)
        self.day_option.grid(row=0, column=2, padx=(0, 10))

        self.hour_option = customtkinter.CTkOptionMenu(self.deadline_frame, values=hours, font=self.default_font, width=60)
        self.hour_option.grid(row=0, column=3, padx=(0, 5))

        self.minute_option = customtkinter.CTkOptionMenu(self.deadline_frame, values=minutes, font=self.default_font, width=60)
        self.minute_option.grid(row=0, column=4, padx=(0, 0))

        self.add_task_btn = customtkinter.CTkButton(self.todo_header, text="添加", font=self.default_font, width=60, height=35, command=self.add_task_event)
        self.add_task_btn.grid(row=0, column=3)

        # 待办事项: 状态标签
        self.uncompleted_label = customtkinter.CTkLabel(self.todo_frame, text="未完成：0 项", font=self.default_font, text_color="gray60")
        self.uncompleted_label.grid(row=1, column=0, sticky="w", padx=25, pady=(0, 10))

        # 待办事项: 任务列表
        self.todo_list_frame = customtkinter.CTkScrollableFrame(self.todo_frame, fg_color="transparent")
        self.todo_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 20))


        # 密码管理页面
        self.password_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.password_frame.grid_columnconfigure(0, weight=1)
        self.password_frame.grid_rowconfigure(0, weight=1)


        # 密码主框架（已解锁状态）
        self.password_main_frame = customtkinter.CTkFrame(self.password_frame, fg_color="transparent")
        self.password_main_frame.grid_columnconfigure(0, weight=3) # 左侧列表
        self.password_main_frame.grid_columnconfigure(1, weight=5) # 右侧详情
        self.password_main_frame.grid_rowconfigure(0, weight=1)

        # === 左侧面板 (密码列表) ===
        self.pwd_left_frame = customtkinter.CTkFrame(self.password_main_frame, fg_color="#252526")
        self.pwd_left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.pwd_left_frame.grid_rowconfigure(2, weight=1)
        self.pwd_left_frame.grid_columnconfigure(0, weight=1)
        self.pwd_left_frame.grid_columnconfigure(1, weight=1)

        # 搜索和筛选
        self.pwd_search_entry = customtkinter.CTkEntry(self.pwd_left_frame, placeholder_text="搜索...", font=self.default_font)
        self.pwd_search_entry.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))

        self.pwd_tag_filter = customtkinter.CTkOptionMenu(self.pwd_left_frame, values=["全部", "工作", "个人", "金融", "其他"], font=self.default_font)
        self.pwd_tag_filter.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        # 密码列表 (滚动)
        self.pwd_list_frame = customtkinter.CTkScrollableFrame(self.pwd_left_frame, fg_color="transparent")
        self.pwd_list_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=(0, 10))

        # 新增按钮 (放置在左下角)
        self.pwd_add_btn = customtkinter.CTkButton(self.pwd_left_frame, text="+ 添加新密码", font=self.default_font, command=self.prepare_add_password)
        self.pwd_add_btn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))




        # 绑定搜索和筛选事件
        self.pwd_search_entry.bind("<KeyRelease>", self.refresh_password_list)
        self.pwd_tag_filter.configure(command=self.refresh_password_list)

        # === 右侧面板 (详情编辑) ===

        self.pwd_right_frame = customtkinter.CTkFrame(self.password_main_frame, fg_color="#2b2b2b")
        self.pwd_right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.pwd_right_frame.grid_columnconfigure(1, weight=1)

        row_idx = 0

        # 网站/应用名
        lbl1 = customtkinter.CTkLabel(self.pwd_right_frame, text="网站/应用名：", font=self.default_font)
        lbl1.grid(row=row_idx, column=0, sticky="e", padx=(20, 10), pady=(20, 10))
        self.pwd_site_entry = customtkinter.CTkEntry(self.pwd_right_frame, font=self.default_font)
        self.pwd_site_entry.grid(row=row_idx, column=1, columnspan=2, sticky="ew", padx=(0, 20), pady=(20, 10))
        row_idx += 1

        # 用户名
        lbl2 = customtkinter.CTkLabel(self.pwd_right_frame, text="用户名：", font=self.default_font)
        lbl2.grid(row=row_idx, column=0, sticky="e", padx=(20, 10), pady=10)
        self.pwd_user_entry = customtkinter.CTkEntry(self.pwd_right_frame, font=self.default_font)
        self.pwd_user_entry.grid(row=row_idx, column=1, columnspan=2, sticky="ew", padx=(0, 20), pady=10)
        row_idx += 1

        # 密码
        lbl3 = customtkinter.CTkLabel(self.pwd_right_frame, text="密码：", font=self.default_font)
        lbl3.grid(row=row_idx, column=0, sticky="e", padx=(20, 10), pady=10)

        self.pwd_pwd_entry = customtkinter.CTkEntry(self.pwd_right_frame, font=self.default_font, show="•")
        self.pwd_pwd_entry.grid(row=row_idx, column=1, sticky="ew", padx=(0, 5), pady=10)

        self.pwd_toggle_btn = customtkinter.CTkButton(self.pwd_right_frame, text="👁", width=30, font=self.default_font, command=self.toggle_password_visibility)
        self.pwd_toggle_btn.grid(row=row_idx, column=2, sticky="w", padx=(0, 20), pady=10)
        row_idx += 1

        # 密码生成 & 复制
        self.pwd_gen_btn = customtkinter.CTkButton(self.pwd_right_frame, text="生成随机密码", font=self.default_font, command=self.generate_random_password)
        self.pwd_gen_btn.grid(row=row_idx, column=1, sticky="w", padx=0, pady=(0, 10))

        self.pwd_copy_btn = customtkinter.CTkButton(self.pwd_right_frame, text="一键复制", font=self.default_font, command=self.copy_password)
        self.pwd_copy_btn.grid(row=row_idx, column=2, sticky="w", padx=(0, 20), pady=(0, 10))
        row_idx += 1

        # 分类标签
        lbl4 = customtkinter.CTkLabel(self.pwd_right_frame, text="分类标签：", font=self.default_font)
        lbl4.grid(row=row_idx, column=0, sticky="e", padx=(20, 10), pady=10)
        self.pwd_tag_combo = customtkinter.CTkOptionMenu(self.pwd_right_frame, values=["工作", "个人", "金融", "其他"], font=self.default_font)
        self.pwd_tag_combo.grid(row=row_idx, column=1, columnspan=2, sticky="ew", padx=(0, 20), pady=10)
        row_idx += 1

        # 备注
        lbl5 = customtkinter.CTkLabel(self.pwd_right_frame, text="备注：", font=self.default_font)
        lbl5.grid(row=row_idx, column=0, sticky="ne", padx=(20, 10), pady=10)
        self.pwd_notes_text = customtkinter.CTkTextbox(self.pwd_right_frame, font=self.default_font, height=100)
        self.pwd_notes_text.grid(row=row_idx, column=1, columnspan=2, sticky="ew", padx=(0, 20), pady=10)
        row_idx += 1

        # 操作按钮区
        self.pwd_action_frame = customtkinter.CTkFrame(self.pwd_right_frame, fg_color="transparent")
        self.pwd_action_frame.grid(row=row_idx, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        self.pwd_action_frame.grid_columnconfigure(0, weight=1)
        self.pwd_action_frame.grid_columnconfigure(1, weight=1)

        self.pwd_save_btn = customtkinter.CTkButton(self.pwd_action_frame, text="保存", font=self.default_font, command=self.save_password_item)
        self.pwd_save_btn.grid(row=0, column=0, padx=10, sticky="e")

        self.pwd_delete_btn = customtkinter.CTkButton(self.pwd_action_frame, text="删除", font=self.default_font, fg_color="#c9302c", hover_color="#ac2925", command=self.delete_password_item)
        self.pwd_delete_btn.grid(row=0, column=1, padx=10, sticky="w")

        self.current_editing_index = -1

        # 密码解锁/设置框架（未解锁状态）
        self.password_auth_frame = customtkinter.CTkFrame(self.password_frame, fg_color="transparent")
        self.password_auth_frame.grid_columnconfigure(0, weight=1)
        self.password_auth_frame.grid_rowconfigure(0, weight=1)
        self.password_auth_frame.grid_rowconfigure(3, weight=1)

        self.auth_title = customtkinter.CTkLabel(self.password_auth_frame, text="欢迎使用密码本", font=customtkinter.CTkFont(family="MiSans", size=32, weight="bold"))
        self.auth_title.grid(row=1, column=0, pady=(0, 20))

        self.auth_entry = customtkinter.CTkEntry(self.password_auth_frame, font=self.default_font, show="*", width=300, placeholder_text="请输入主密码")
        self.auth_entry.grid(row=2, column=0, pady=10)

        self.auth_btn = customtkinter.CTkButton(self.password_auth_frame, text="确 认", font=self.default_font, command=self.unlock_vault)
        self.auth_btn.grid(row=3, column=0, pady=10, sticky="n")

        # 桌面整理页面
        self.desktop_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.desktop_frame.grid_columnconfigure(0, weight=1)
        self.desktop_frame.grid_rowconfigure(0, weight=1)
        self.desktop_label = customtkinter.CTkLabel(self.desktop_frame, text="桌面整理", font=customtkinter.CTkFont(family="MiSans", size=40, weight="bold"))
        self.desktop_label.grid(row=0, column=0, sticky="nsew")

        # 设置页面 (占位)
        self.settings_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.settings_frame.grid_rowconfigure(0, weight=1)
        self.settings_label = customtkinter.CTkLabel(self.settings_frame, text="设置", font=customtkinter.CTkFont(family="MiSans", size=40, weight="bold"))
        self.settings_label.grid(row=0, column=0, sticky="nsew")

        # 密码本状态
        self.vault_unlocked = False
        self.vault = None


        # 初始化时，默认选中并显示待办事项页面
        self.select_frame_by_name("待办事项")

        # 初始化截止时间为当前时间
        self._reset_deadline_to_current_time()

        # 载入数据
        self.load_tasks()

    def _reset_deadline_to_current_time(self):
        now = datetime.datetime.now()
        self.year_option.set(str(now.year))
        self.month_option.set(f"{now.month:02d}")
        self.day_option.set(f"{now.day:02d}")
        self.hour_option.set(f"{now.hour:02d}")
        self.minute_option.set(f"{now.minute:02d}")

    def add_task_event(self):
        text = self.task_entry.get().strip()
        if not text:
            return

        priority = self.priority_option.get()

        y = self.year_option.get()
        m = self.month_option.get()
        d = self.day_option.get()
        h = self.hour_option.get()
        minute = self.minute_option.get()
        deadline = f"{y}-{m}-{d} {h}:{minute}"

        new_task = {
            "text": text,
            "priority": priority,
            "deadline": deadline,
            "completed": False
        }

        self.tasks.append(new_task)
        self.save_tasks()

        self.task_entry.delete(0, 'end')
        self._reset_deadline_to_current_time()

        self.refresh_task_list()

    def load_tasks(self):
        self.tasks = []
        file_path = os.path.join(os.path.dirname(__file__), "todo_data.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except Exception:
                self.tasks = []
        self.refresh_task_list()

    def save_tasks(self):
        file_path = os.path.join(os.path.dirname(__file__), "todo_data.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存失败: {e}")

    def refresh_task_list(self):
        # 清空现有列表
        for widget in self.todo_list_frame.winfo_children():
            widget.destroy()

        uncompleted_count = sum(1 for task in self.tasks if not task.get("completed"))
        self.uncompleted_label.configure(text=f"未完成：{uncompleted_count} 项")

        priority_colors = {
            "普通": "gray",
            "重要": "orange",
            "紧急": "red"
        }

        for i, task in enumerate(self.tasks):
            task_frame = customtkinter.CTkFrame(self.todo_list_frame, fg_color="#2b2b2b", corner_radius=5)
            task_frame.grid(row=i, column=0, sticky="ew", padx=10, pady=5)
            self.todo_list_frame.grid_columnconfigure(0, weight=1)
            task_frame.grid_columnconfigure(2, weight=1) # 文本标签拉伸

            # 优先级圆点
            color = priority_colors.get(task.get("priority", "普通"), "gray")
            dot = customtkinter.CTkFrame(task_frame, width=10, height=10, corner_radius=5, fg_color=color)
            dot.grid(row=0, column=0, padx=(10, 5), pady=10)

            # 复选框
            checkbox = customtkinter.CTkCheckBox(
                task_frame, text="", width=24,
                command=lambda index=i: self.toggle_task(index)
            )
            if task.get("completed"):
                checkbox.select()
            else:
                checkbox.deselect()
            checkbox.grid(row=0, column=1, padx=5, pady=10)

            # 任务文字
            is_completed = task.get("completed", False)
            current_font = self.strike_font if is_completed else self.default_font
            current_color = "gray50" if is_completed else ("gray10", "gray90")

            task_label = customtkinter.CTkLabel(
                task_frame, text=task.get("text", ""), font=current_font, text_color=current_color, anchor="w"
            )
            task_label.grid(row=0, column=2, sticky="ew", padx=10, pady=10)

            # 绑定双击事件到文字标签
            task_label.bind("<Double-Button-1>", lambda event, index=i, lbl=task_label, frm=task_frame: self.start_edit_task(index, lbl, frm))

            # 截止时间
            deadline = task.get("deadline", "")
            if deadline:
                deadline_label = customtkinter.CTkLabel(
                    task_frame, text=deadline, font=customtkinter.CTkFont(family="MiSans", size=12), text_color="gray60"
                )
                deadline_label.grid(row=0, column=3, padx=10, pady=10)

            # 删除按钮
            del_btn = customtkinter.CTkButton(
                task_frame, text="✕", width=30, height=30, fg_color="transparent", hover_color="#ff4a4a",
                font=self.default_font, command=lambda index=i: self.delete_task(index)
            )
            del_btn.grid(row=0, column=4, padx=(5, 10), pady=10)

    def delete_task(self, index):
        if 0 <= index < len(self.tasks):
            del self.tasks[index]
            self.save_tasks()
            self.refresh_task_list()

    def toggle_task(self, index):
        if 0 <= index < len(self.tasks):
            self.tasks[index]["completed"] = not self.tasks[index].get("completed", False)
            self.save_tasks()
            self.refresh_task_list()

    def start_edit_task(self, index, label, frame):
        # 隐藏原来的标签
        label.grid_remove()

        # 创建一个输入框
        edit_entry = customtkinter.CTkEntry(frame, font=self.default_font)
        edit_entry.insert(0, self.tasks[index].get("text", ""))
        edit_entry.grid(row=0, column=2, sticky="ew", padx=10, pady=10)
        edit_entry.focus()

        # 绑定回车和失去焦点事件
        edit_entry.bind("<Return>", lambda event, i=index, e=edit_entry, l=label: self.finish_edit_task(event, i, e, l))
        edit_entry.bind("<FocusOut>", lambda event, i=index, e=edit_entry, l=label: self.finish_edit_task(event, i, e, l))

    def finish_edit_task(self, event, index, entry, label):
        if not entry.winfo_exists():
            return

        new_text = entry.get().strip()
        if new_text:
            self.tasks[index]["text"] = new_text
            self.save_tasks()

        entry.destroy()

        # 重新显示标签，或者直接刷新列表
        self.refresh_task_list()

    def center_window(self, width, height):
        # 获取屏幕宽度和高度
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # 计算 x 和 y 坐标
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)

        self.geometry('%dx%d+%d+%d' % (width, height, x, y))

    def select_frame_by_name(self, name):
        # 1. 设置所有按钮的颜色，以实现选中态和非选中态的视觉区分
        # 被选中的按钮颜色变深，未选中的恢复透明背景
        self.todo_button.configure(fg_color=("gray75", "gray25") if name == "待办事项" else "transparent")
        self.password_button.configure(fg_color=("gray75", "gray25") if name == "密码管理" else "transparent")
        self.desktop_button.configure(fg_color=("gray75", "gray25") if name == "桌面整理" else "transparent")
        self.settings_button.configure(fg_color=("gray75", "gray25") if name == "设置" else "transparent")

        # 2. 隐藏所有页面，然后再显示需要的页面
        # 隐藏
        self.todo_frame.grid_forget()
        self.password_frame.grid_forget()
        self.desktop_frame.grid_forget()
        self.settings_frame.grid_forget()

        # 3. 根据名称显示对应的页面
        if name == "待办事项":
            self.todo_frame.grid(row=0, column=1, sticky="nsew")
        elif name == "密码管理":
            self.password_frame.grid(row=0, column=1, sticky="nsew")
            self.show_password_view()
        elif name == "桌面整理":
            self.desktop_frame.grid(row=0, column=1, sticky="nsew")
        elif name == "设置":
            self.settings_frame.grid(row=0, column=1, sticky="nsew")




    def prepare_add_password(self):
        self.pwd_site_entry.delete(0, 'end')
        self.pwd_user_entry.delete(0, 'end')
        self.pwd_pwd_entry.delete(0, 'end')
        self.pwd_notes_text.delete("1.0", 'end')
        self.pwd_tag_combo.set("其他")
        self.current_editing_index = -1

    def toggle_password_visibility(self):
        if self.pwd_pwd_entry.cget("show") == "":
            self.pwd_pwd_entry.configure(show="•")
        else:
            self.pwd_pwd_entry.configure(show="")

    def generate_random_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
        while True:
            pwd = ''.join(secrets.choice(chars) for _ in range(18))
            if (any(c.islower() for c in pwd) and
                any(c.isupper() for c in pwd) and
                any(c.isdigit() for c in pwd) and
                any(c in "!@#$%^&*()_+-=" for c in pwd)):
                break
        self.pwd_pwd_entry.delete(0, 'end')
        self.pwd_pwd_entry.insert(0, pwd)
        self.pwd_pwd_entry.configure(show="")

    def copy_password(self):
        pwd = self.pwd_pwd_entry.get()
        if pwd:
            self.clipboard_clear()
            self.clipboard_append(pwd)
            tkinter.messagebox.showinfo("成功", "密码已复制到剪贴板")



    def save_password_item(self):
        site = self.pwd_site_entry.get().strip()
        user = self.pwd_user_entry.get().strip()
        pwd = self.pwd_pwd_entry.get()
        tag = self.pwd_tag_combo.get()
        notes = self.pwd_notes_text.get("1.0", "end-1c").strip()

        if not site or not pwd:
            tkinter.messagebox.showerror("错误", "网站/应用名和密码不能为空！")
            return

        item = {
            "site": site,
            "user": user,
            "password": pwd,
            "tag": tag,
            "notes": notes
        }

        if self.current_editing_index >= 0 and self.current_editing_index < len(self.vault.passwords):
            self.vault.passwords[self.current_editing_index] = item
        else:
            self.vault.passwords.append(item)

        self.vault.save()
        self.refresh_password_list()
        tkinter.messagebox.showinfo("成功", "保存成功")

    def delete_password_item(self):
        if self.current_editing_index >= 0 and self.current_editing_index < len(self.vault.passwords):
            del self.vault.passwords[self.current_editing_index]
            self.vault.save()
            self.prepare_add_password()
            self.refresh_password_list()
            tkinter.messagebox.showinfo("成功", "删除成功")

    def edit_password_item(self, index):
        if 0 <= index < len(self.vault.passwords):
            self.current_editing_index = index
            item = self.vault.passwords[index]

            self.pwd_site_entry.delete(0, 'end')
            self.pwd_site_entry.insert(0, item.get("site", ""))

            self.pwd_user_entry.delete(0, 'end')
            self.pwd_user_entry.insert(0, item.get("user", ""))

            self.pwd_pwd_entry.delete(0, 'end')
            self.pwd_pwd_entry.insert(0, item.get("password", ""))
            self.pwd_pwd_entry.configure(show="•")

            self.pwd_tag_combo.set(item.get("tag", "其他"))

            self.pwd_notes_text.delete("1.0", 'end')
            self.pwd_notes_text.insert("1.0", item.get("notes", ""))



    def refresh_password_list(self, *args):
        for widget in self.pwd_list_frame.winfo_children():
            widget.destroy()

        if not self.vault:
            return

        search_kw = self.pwd_search_entry.get().lower()
        filter_tag = self.pwd_tag_filter.get()

        for i, item in enumerate(self.vault.passwords):
            site = item.get("site", "")
            user = item.get("user", "")
            tag = item.get("tag", "")

            if filter_tag != "全部" and tag != filter_tag:
                continue
            if search_kw and search_kw not in site.lower() and search_kw not in user.lower():
                continue

            frame = customtkinter.CTkFrame(self.pwd_list_frame, fg_color="#333333", corner_radius=5)
            frame.grid(row=i, column=0, sticky="ew", padx=5, pady=5)
            self.pwd_list_frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            # 点击整个frame或者文字进行编辑
            lbl = customtkinter.CTkLabel(frame, text=f"{site}\n{user}", font=self.default_font, anchor="w", justify="left")
            lbl.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

            lbl.bind("<Button-1>", lambda e, idx=i: self.edit_password_item(idx))

            # 上移/下移
            up_btn = customtkinter.CTkButton(frame, text="↑", width=25, command=lambda idx=i: self.move_password(idx, -1))
            up_btn.grid(row=0, column=1, padx=(5, 2))

            dn_btn = customtkinter.CTkButton(frame, text="↓", width=25, command=lambda idx=i: self.move_password(idx, 1))
            dn_btn.grid(row=0, column=2, padx=(2, 5))

    def move_password(self, index, direction):
        new_index = index + direction
        if 0 <= new_index < len(self.vault.passwords):
            self.vault.passwords.insert(new_index, self.vault.passwords.pop(index))
            self.vault.save()
            self.refresh_password_list()

    def show_password_view(self):
        if self.vault_unlocked:
            self.password_auth_frame.grid_forget()
            self.password_main_frame.grid(row=0, column=0, sticky="nsew")
            # 刷新列表等
            self.refresh_password_list()
            self.prepare_add_password()
        else:
            self.password_main_frame.grid_forget()
            self.password_auth_frame.grid(row=0, column=0, sticky="nsew")
            self.auth_entry.delete(0, 'end')

            vault_file = os.path.join(os.path.dirname(__file__), "vault.enc")
            if not os.path.exists(vault_file):
                self.auth_title.configure(text="首次使用，请设置主密码\n（重要：忘记无法恢复！）")
                self.auth_btn.configure(text="设 置", command=self.setup_master_password)
            else:
                self.auth_title.configure(text="请输入主密码解锁")
                self.auth_btn.configure(text="解 锁", command=self.unlock_vault)

    def setup_master_password(self):
        pwd = self.auth_entry.get()
        if not pwd:
            tkinter.messagebox.showerror("错误", "密码不能为空！")
            return

        self.vault = PasswordVault(pwd)
        self.vault.setup_new()
        self.vault_unlocked = True
        self.show_password_view()

    def unlock_vault(self):
        pwd = self.auth_entry.get()
        if not pwd:
            tkinter.messagebox.showerror("错误", "密码不能为空！")
            return

        vault = PasswordVault(pwd)
        if vault.load():
            self.vault = vault
            self.vault_unlocked = True
            self.show_password_view()
        else:
            tkinter.messagebox.showerror("错误", "密码错误，解锁失败！")
            self.auth_entry.delete(0, 'end')

    def todo_button_event(self):
        # 点击“待办事项”按钮触发的事件
        self.select_frame_by_name("待办事项")

    def password_button_event(self):
        # 点击“密码管理”按钮触发的事件
        self.select_frame_by_name("密码管理")

    def desktop_button_event(self):
        # 点击“桌面整理”按钮触发的事件
        self.select_frame_by_name("桌面整理")

    def settings_button_event(self):
        # 点击“设置”按钮触发的事件
        self.select_frame_by_name("设置")

if __name__ == "__main__":
    app = App()
    app.mainloop()
