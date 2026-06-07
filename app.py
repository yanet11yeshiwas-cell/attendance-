# app.py
import customtkinter as ctk
import pages

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.geometry("600x500")
        self.title("Attendance Management System")

        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self.frames = {}
        pages_list = [pages.WelcomePage, pages.AdminLoginPage, pages.AdminPanelPage,
                      pages.UserPage, pages.ReportPage]

        for PageClass in pages_list:
            frame = PageClass(parent=container, controller=self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[PageClass] = frame

        self.show_frame(pages.WelcomePage)

    def show_frame(self, page_class):
        frame = self.frames[page_class]
        frame.tkraise()

if __name__ == "__main__":
    app = App()
    app.mainloop()
