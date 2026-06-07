# pages.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
import sqlite3
import pandas as pd
import os
import subprocess
import platform
from datetime import datetime

# ------------------ Database Helper ------------------
class Database:
    def __init__(self, db_path="attendance.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Students table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        # Attendance table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT,
                status TEXT,
                FOREIGN KEY (student_id) REFERENCES students (id),
                UNIQUE(student_id, date)
            )
        ''')
        # Admin table (default password: admin123)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        self.cursor.execute("SELECT * FROM admin")
        if not self.cursor.fetchone():
            self.cursor.execute("INSERT INTO admin (id, password) VALUES (1, 'admin123')")
        self.conn.commit()

    def get_students(self):
        self.cursor.execute("SELECT id, name FROM students ORDER BY name")
        return self.cursor.fetchall()

    def add_student(self, name):
        try:
            self.cursor.execute("INSERT INTO students (name) VALUES (?)", (name.strip(),))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_student(self, student_id):
        self.cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        self.cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        self.conn.commit()

    def mark_attendance(self, student_id, date, status):
        try:
            self.cursor.execute('''
                INSERT INTO attendance (student_id, date, status)
                VALUES (?, ?, ?)
            ''', (student_id, date, status))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # duplicate

    def get_attendance_range(self, start_date, end_date):
        query = '''
            SELECT s.name, a.date, a.status
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date BETWEEN ? AND ?
            ORDER BY a.date, s.name
        '''
        self.cursor.execute(query, (start_date, end_date))
        return self.cursor.fetchall()

    def verify_admin(self, password):
        self.cursor.execute("SELECT password FROM admin WHERE id = 1")
        stored = self.cursor.fetchone()
        return stored and stored[0] == password

    def close(self):
        self.conn.close()

db = Database()

# ------------------ Helper: open file cross-platform ------------------
def open_file_with_default_app(filepath):
    if platform.system() == "Windows":
        os.startfile(filepath)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", filepath])
    else:  # Linux
        subprocess.run(["xdg-open", filepath])

# ------------------ Welcome Page ------------------
class WelcomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(main_frame, text="Attendance Management System",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=20)

        ctk.CTkButton(main_frame, text="Student Mode", width=200,
                      command=lambda: controller.show_frame(UserPage)).grid(row=1, column=0, pady=10)
        ctk.CTkButton(main_frame, text="Admin Mode", width=200,
                      command=lambda: controller.show_frame(AdminLoginPage)).grid(row=2, column=0, pady=10)
        ctk.CTkButton(main_frame, text="Exit", width=200, command=self.quit).grid(row=3, column=0, pady=10)

# ------------------ Admin Login Page ------------------
class AdminLoginPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Admin Login", font=ctk.CTkFont(size=20)).grid(row=0, column=0, pady=10)
        ctk.CTkLabel(frame, text="Password:").grid(row=1, column=0, pady=5)
        self.pw_entry = ctk.CTkEntry(frame, show="*", width=200)
        self.pw_entry.grid(row=2, column=0, pady=5)
        ctk.CTkButton(frame, text="Login", command=self.check_login).grid(row=3, column=0, pady=10)
        ctk.CTkButton(frame, text="Back", command=lambda: controller.show_frame(WelcomePage)).grid(row=4, column=0, pady=5)

    def check_login(self):
        if db.verify_admin(self.pw_entry.get()):
            self.controller.show_frame(AdminPanelPage)
        else:
            messagebox.showerror("Login Failed", "Incorrect password")

# ------------------ Admin Panel Page ------------------
class AdminPanelPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=0)
        main_frame.grid_rowconfigure(1, weight=0)
        main_frame.grid_rowconfigure(2, weight=1)

        # Student management section
        student_frame = ctk.CTkFrame(main_frame)
        student_frame.grid(row=0, column=0, sticky="ew", pady=5)
        student_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(student_frame, text="Student Management", font=ctk.CTkFont(size=16)).grid(row=0, column=0, pady=5)

        add_frame = ctk.CTkFrame(student_frame)
        add_frame.grid(row=1, column=0, pady=5)
        self.new_student_entry = ctk.CTkEntry(add_frame, placeholder_text="New student name", width=200)
        self.new_student_entry.pack(side="left", padx=5)
        ctk.CTkButton(add_frame, text="Add Student", command=self.add_student).pack(side="left", padx=5)

        self.student_listbox = tk.Listbox(student_frame, height=6)
        self.student_listbox.grid(row=2, column=0, sticky="ew", pady=5)
        ctk.CTkButton(student_frame, text="Delete Selected Student", command=self.delete_student,
                      fg_color="red").grid(row=3, column=0, pady=5)

        # Report section
        report_frame = ctk.CTkFrame(main_frame)
        report_frame.grid(row=1, column=0, sticky="ew", pady=10)
        report_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(report_frame, text="Generate Report", font=ctk.CTkFont(size=16)).grid(row=0, column=0, pady=5)

        date_frame = ctk.CTkFrame(report_frame)
        date_frame.grid(row=1, column=0, pady=5)
        ctk.CTkLabel(date_frame, text="From:").pack(side="left", padx=5)
        self.start_date = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.start_date.pack(side="left", padx=5)
        ctk.CTkLabel(date_frame, text="To:").pack(side="left", padx=5)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_date.pack(side="left", padx=5)
        ctk.CTkButton(report_frame, text="View / Export Report",
                      command=lambda: controller.show_frame(ReportPage)).grid(row=2, column=0, pady=5)

        # Logout
        ctk.CTkButton(main_frame, text="Logout", command=self.logout, fg_color="gray").grid(row=2, column=0, pady=10, sticky="s")

        self.refresh_student_list()

    def refresh_student_list(self):
        self.student_listbox.delete(0, tk.END)
        for sid, name in db.get_students():
            self.student_listbox.insert(tk.END, f"{sid}: {name}")

    def add_student(self):
        name = self.new_student_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Student name cannot be empty")
            return
        if db.add_student(name):
            messagebox.showinfo("Success", f"Student '{name}' added")
            self.new_student_entry.delete(0, tk.END)
            self.refresh_student_list()
        else:
            messagebox.showerror("Error", "Student already exists")

    def delete_student(self):
        selection = self.student_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a student to delete")
            return
        item = self.student_listbox.get(selection[0])
        student_id = int(item.split(":")[0])
        if messagebox.askyesno("Confirm", f"Delete student and all attendance records?"):
            db.delete_student(student_id)
            self.refresh_student_list()
            messagebox.showinfo("Success", "Student deleted")

    def logout(self):
        self.controller.show_frame(WelcomePage)

# ------------------ User (Student) Page ------------------
class UserPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(main_frame, text="Mark Attendance", font=ctk.CTkFont(size=20)).grid(row=0, column=0, pady=10)

        ctk.CTkLabel(main_frame, text="Select Student:").grid(row=1, column=0, pady=5)
        self.student_var = tk.StringVar()
        self.student_combo = ctk.CTkComboBox(main_frame, values=[], variable=self.student_var, width=250)
        self.student_combo.grid(row=2, column=0, pady=5)

        ctk.CTkLabel(main_frame, text="Date:").grid(row=3, column=0, pady=5)
        self.date_picker = DateEntry(main_frame, width=16, background='darkblue', foreground='white')
        self.date_picker.grid(row=4, column=0, pady=5)

        ctk.CTkLabel(main_frame, text="Status:").grid(row=5, column=0, pady=5)
        self.status_var = tk.StringVar(value="Present")
        status_menu = ctk.CTkComboBox(main_frame, values=["Present", "Late", "Absent"], variable=self.status_var)
        status_menu.grid(row=6, column=0, pady=5)

        ctk.CTkButton(main_frame, text="Submit", command=self.submit_attendance).grid(row=7, column=0, pady=10)
        ctk.CTkButton(main_frame, text="Back", command=lambda: controller.show_frame(WelcomePage)).grid(row=8, column=0, pady=5)

        self.refresh_student_list()

    def refresh_student_list(self):
        students = [f"{name}" for _, name in db.get_students()]
        self.student_combo.configure(values=students)
        if students:
            self.student_combo.set(students[0])

    def submit_attendance(self):
        student_name = self.student_var.get().strip()
        if not student_name:
            messagebox.showwarning("Warning", "Please select a student")
            return
        # Get student id
        students = db.get_students()
        student_id = None
        for sid, name in students:
            if name == student_name:
                student_id = sid
                break
        if not student_id:
            messagebox.showerror("Error", "Student not found")
            return

        date_obj = self.date_picker.get_date()
        date_str = date_obj.strftime("%Y-%m-%d")
        status = self.status_var.get()

        if db.mark_attendance(student_id, date_str, status):
            messagebox.showinfo("Success", f"Attendance marked for {student_name} on {date_str}")
        else:
            messagebox.showerror("Error", "Attendance already recorded for this student on this date")

# ------------------ Report Page ------------------
class ReportPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Date selection
        filter_frame = ctk.CTkFrame(main_frame)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=5)
        ctk.CTkLabel(filter_frame, text="From:").pack(side="left", padx=5)
        self.start_date = DateEntry(filter_frame, width=12)
        self.start_date.pack(side="left", padx=5)
        ctk.CTkLabel(filter_frame, text="To:").pack(side="left", padx=5)
        self.end_date = DateEntry(filter_frame, width=12)
        self.end_date.pack(side="left", padx=5)
        ctk.CTkButton(filter_frame, text="Refresh", command=self.load_report).pack(side="left", padx=10)

        # Treeview for report
        self.tree_frame = ctk.CTkFrame(main_frame)
        self.tree_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        columns = ("Student Name", "Date", "Status")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Buttons
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.grid(row=2, column=0, pady=10)
        ctk.CTkButton(btn_frame, text="Export to CSV", command=self.export_csv).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Back to Admin", command=self.back_to_admin).pack(side="left", padx=5)

        self.load_report()

    def load_report(self):
        start = self.start_date.get_date().strftime("%Y-%m-%d")
        end = self.end_date.get_date().strftime("%Y-%m-%d")
        data = db.get_attendance_range(start, end)

        for row in self.tree.get_children():
            self.tree.delete(row)

        for name, date, status in data:
            self.tree.insert("", "end", values=(name, date, status))

    def export_csv(self):
        start = self.start_date.get_date().strftime("%Y-%m-%d")
        end = self.end_date.get_date().strftime("%Y-%m-%d")
        data = db.get_attendance_range(start, end)

        if not data:
            messagebox.showinfo("No Data", "No records found for the selected period")
            return

        df = pd.DataFrame(data, columns=["Student Name", "Date", "Status"])
        filename = f"attendance_{start}_to_{end}.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Export Complete", f"Saved as {filename}\nOpen file?")
        if messagebox.askyesno("Open", "Open the exported file?"):
            open_file_with_default_app(os.path.abspath(filename))

    def back_to_admin(self):
        self.controller.show_frame(AdminPanelPage)

# Required import for Treeview
from tkinter import ttk
