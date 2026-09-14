import customtkinter

# 设置整体外观和颜色主题
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

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
        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text="  井 然", font=customtkinter.CTkFont(size=24, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=(20, 40))

        # 待办事项按钮
        self.todo_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="待办事项",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   anchor="w", command=self.todo_button_event)
        self.todo_button.grid(row=1, column=0, sticky="ew")

        # 密码管理按钮
        self.password_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="密码管理",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      anchor="w", command=self.password_button_event)
        self.password_button.grid(row=2, column=0, sticky="ew")

        # 桌面整理按钮
        self.desktop_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="桌面整理",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      anchor="w", command=self.desktop_button_event)
        self.desktop_button.grid(row=3, column=0, sticky="ew")

        # 设置按钮 (固定在底部)
        self.settings_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="设置",
                                                       fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                       anchor="w", command=self.settings_button_event)
        self.settings_button.grid(row=5, column=0, sticky="ew", pady=(0, 20))


        # ============ 右侧内容区 ============

        # 待办事项页面
        self.todo_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.todo_frame.grid_columnconfigure(0, weight=1)
        self.todo_frame.grid_rowconfigure(0, weight=1)
        self.todo_label = customtkinter.CTkLabel(self.todo_frame, text="待办事项", font=customtkinter.CTkFont(size=40, weight="bold"))
        self.todo_label.grid(row=0, column=0, sticky="nsew")

        # 密码管理页面
        self.password_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.password_frame.grid_columnconfigure(0, weight=1)
        self.password_frame.grid_rowconfigure(0, weight=1)
        self.password_label = customtkinter.CTkLabel(self.password_frame, text="密码管理", font=customtkinter.CTkFont(size=40, weight="bold"))
        self.password_label.grid(row=0, column=0, sticky="nsew")

        # 桌面整理页面
        self.desktop_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.desktop_frame.grid_columnconfigure(0, weight=1)
        self.desktop_frame.grid_rowconfigure(0, weight=1)
        self.desktop_label = customtkinter.CTkLabel(self.desktop_frame, text="桌面整理", font=customtkinter.CTkFont(size=40, weight="bold"))
        self.desktop_label.grid(row=0, column=0, sticky="nsew")

        # 设置页面 (占位)
        self.settings_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.settings_frame.grid_rowconfigure(0, weight=1)
        self.settings_label = customtkinter.CTkLabel(self.settings_frame, text="设置", font=customtkinter.CTkFont(size=40, weight="bold"))
        self.settings_label.grid(row=0, column=0, sticky="nsew")


        # 初始化时，默认选中并显示待办事项页面
        self.select_frame_by_name("待办事项")

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
        elif name == "桌面整理":
            self.desktop_frame.grid(row=0, column=1, sticky="nsew")
        elif name == "设置":
            self.settings_frame.grid(row=0, column=1, sticky="nsew")

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
