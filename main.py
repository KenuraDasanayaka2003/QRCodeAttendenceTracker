import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import sqlite3
import qrcode
import os
import cv2
from pyzbar.pyzbar import decode
from datetime import datetime

#========================DATABASE SETUP=================================
def init_db():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT
        )
        """)

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS attendance (
        student_id INTEGER,
        date TEXT,
        time TEXT
        )
        """)
    conn.commit()
    conn.close()

init_db()

#=======================REGISTER STUDENT=====================================
def register_student():
    name = entry_name.get()
    email = entry_email.get()

    if name == "":
        messagebox.showerror("Error", "Name cannot be empty")
        return

    if email == "":
        messagebox.showerror("Error", "Email cannot be empty")
        return

    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    # 1️⃣ Find the lowest available ID
    cursor.execute("SELECT id FROM students ORDER BY id")
    existing_ids = [row[0] for row in cursor.fetchall()]

    # Find the first missing number
    new_id = 1
    for eid in existing_ids:
        if eid == new_id:
            new_id += 1
        else:
            break

    cursor.execute("INSERT INTO students (id, name, email) VALUES (?, ?, ?)",(new_id,name,email))
    student_id = cursor.lastrowid
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "Student registered")

    #GENERATE QR
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")

    qr_data = f"ID:{student_id}"  # <- Unique per student!
    qr = qrcode.make(qr_data)
    qr_file = f"qrcodes/student_{student_id}.png"
    qr.save(qr_file)

    messagebox.showinfo("Success", "Student registered!\nQR Code generated")
    entry_name.delete(0, tk.END)
    entry_email.delete(0, tk.END)

#======================REMOVE STUDENTS==========================================
def delete_student(student_id):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    # 1️⃣ Delete student attendance
    cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))

    # 2️⃣ Delete student record
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))

    qr_file = f"qrcodes/student_{student_id}.png"
    if os.path.exists(qr_file):
        os.remove(qr_file)

        messagebox.showinfo(f"Success","Student with ID deleted successfully.")

    conn.commit()
    conn.close()


#=======================MARK ATTENDANCE===========================================
def mark_attendance(student_id):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")

    # Prevent duplicate attendance
    cursor.execute("""
        SELECT * FROM attendance 
        WHERE student_id=? AND date=?
    """, (student_id, today))

    if cursor.fetchone():
        messagebox.showwarning("Warning", "Attendance already marked today!")
    else:
        cursor.execute("INSERT INTO attendance VALUES (?, ?, ?)",
                       (student_id, today, now_time))
        conn.commit()
        messagebox.showinfo("Success", "Attendance Marked!")

    conn.close()

#====================HANDLE DROP===========================================
def handle_drop(event):
    file_path = event.data.strip("{}")  # remove curly braces

    try:
        img = cv2.imread(file_path)
        decoded_objects = decode(img)

        if decoded_objects:
            qr_data = decoded_objects[0].data.decode("utf-8")

            if "ID:" in qr_data:
                student_id = qr_data.split(":")[1]
                mark_attendance(student_id)
            else:
                messagebox.showerror("Error", "Invalid QR Code")

        else:
            messagebox.showerror("Error", "No QR Code detected")

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ================= VIEW ATTENDANCE =================
def view_attendance():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT students.name, attendance.date, attendance.time
        FROM attendance
        JOIN students ON students.id = attendance.student_id
    """)

    records = cursor.fetchall()
    conn.close()

    result = ""
    for r in records:
        result += f"Name: {r[0]} | Date: {r[1]} | Time: {r[2]}\n"

    if result == "":
        result = "No attendance records found."

    messagebox.showinfo("Attendance Records", result)

# ================= TKINTER GUI =================
root = TkinterDnD.Tk()
root.title("QR Attendance System")
root.geometry("500x500")

tk.Label(root, text="Student Name").pack(pady=10)
entry_name = tk.Entry(root)
entry_name.pack(pady=10)
tk.Label(root, text="Student Email").pack(pady=10)
entry_email = tk.Entry(root)
entry_email.pack(pady=10)


drop_label = tk.Label(root, text="Drag & Drop QR Here",
                      width=40, height=5,
                      bg="light gray")
drop_label.pack(pady=20)

drop_label.drop_target_register(DND_FILES)
drop_label.dnd_bind('<<Drop>>', handle_drop)

tk.Button(root, text="Register Student",
          command=register_student).pack(pady=10)

tk.Label(root, text="Enter Student ID to Delete").pack()
entry_delete = tk.Entry(root)
entry_delete.pack()

tk.Button(root, text="Delete Student", command=lambda: delete_student(entry_delete.get())).pack()

tk.Button(root, text="View Attendance",
          command=view_attendance).pack(pady=10)

root.mainloop()


