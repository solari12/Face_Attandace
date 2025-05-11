import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import os
from datetime import datetime
import sqlite3
from PIL import Image, ImageTk
import threading
import time
import pickle

# Đăng ký adapter cho datetime
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(s):
    return datetime.fromisoformat(s.decode())

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("datetime", convert_datetime)

class AttendanceSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hệ thống chấm công khuôn mặt")
        self.root.geometry("1200x700")
        
        # Khởi tạo database với datetime converter
        self.conn = sqlite3.connect('attendance.db', detect_types=sqlite3.PARSE_DECLTYPES)
        self.cursor = self.conn.cursor()
        
        # Tạo bảng employees
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT,
                department TEXT,
                face_id TEXT UNIQUE
            )
        ''')
        
        # Tạo bảng attendance với kiểu datetime
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                check_in datetime,
                check_out datetime,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')
        
        self.conn.commit()
        
        # Khởi tạo face detector và recognizer
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # Load model và names nếu tồn tại
        if os.path.exists("classifier.xml"):
            self.face_recognizer.read("classifier.xml")
        if os.path.exists("names.pkl"):
            with open("names.pkl", "rb") as f:
                self.names = pickle.load(f)
        else:
            self.names = {}
        
        # Biến để theo dõi trạng thái check-in/out
        self.last_check_in = {}
        
        # Tạo các tab
        self.tab_control = ttk.Notebook(self.root)
        
        # Tab quản lý
        self.management_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.management_tab, text='Quản lý')
        
        # Tab chấm công
        self.attendance_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.attendance_tab, text='Chấm công')
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Khởi tạo giao diện
        self.init_management_tab()
        self.init_attendance_tab()
        
        # Biến cho camera
        self.cap = None
        self.is_capturing = False
        self.current_frame = None
        
    def init_management_tab(self):
        # Frame cho form nhập liệu
        input_frame = ttk.LabelFrame(self.management_tab, text="Thông tin nhân viên")
        input_frame.pack(padx=10, pady=5, fill="x")
        
        # Các trường nhập liệu
        ttk.Label(input_frame, text="Tên:").grid(row=0, column=0, padx=5, pady=5)
        self.name_entry = ttk.Entry(input_frame)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Chức vụ:").grid(row=0, column=2, padx=5, pady=5)
        self.position_entry = ttk.Entry(input_frame)
        self.position_entry.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Phòng ban:").grid(row=1, column=0, padx=5, pady=5)
        self.department_entry = ttk.Entry(input_frame)
        self.department_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Nút Thêm ngay trong form nhập liệu
        self.add_btn = ttk.Button(input_frame, text="Thêm", command=self.add_employee)
        self.add_btn.grid(row=1, column=3, padx=5, pady=5)
        
        # Frame cho camera và danh sách (chia đôi màn hình)
        content_frame = ttk.Frame(self.management_tab)
        content_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Frame bên trái cho camera
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        camera_frame = ttk.LabelFrame(left_frame, text="Camera")
        camera_frame.pack(fill="both", expand=True)
        
        self.camera_label = ttk.Label(camera_frame)
        self.camera_label.pack(padx=5, pady=5)
        
        # Frame cho nút điều khiển camera
        camera_control_frame = ttk.Frame(camera_frame)
        camera_control_frame.pack(padx=5, pady=5)
        
        self.start_camera_btn = ttk.Button(camera_control_frame, text="Bắt đầu camera", command=self.toggle_camera)
        self.start_camera_btn.pack(side="left", padx=5)
        
        self.capture_btn = ttk.Button(camera_control_frame, text="Chụp ảnh", command=self.capture_face, state="disabled")
        self.capture_btn.pack(side="left", padx=5)
        
        # Frame bên phải cho danh sách nhân viên
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)
        
        list_frame = ttk.LabelFrame(right_frame, text="Danh sách nhân viên")
        list_frame.pack(fill="both", expand=True)
        
        # Treeview cho danh sách
        columns = ("ID", "Tên", "Chức vụ", "Phòng ban")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Frame cho nút CRUD
        crud_frame = ttk.Frame(list_frame)
        crud_frame.pack(padx=5, pady=5, fill="x")
        
        ttk.Button(crud_frame, text="Sửa", command=self.edit_employee).pack(side="left", padx=5)
        ttk.Button(crud_frame, text="Xóa", command=self.delete_employee).pack(side="left", padx=5)
        ttk.Button(crud_frame, text="Làm mới", command=self.refresh_employee_list).pack(side="left", padx=5)
        ttk.Button(crud_frame, text="Xem lịch sử", command=self.view_employee_history).pack(side="left", padx=5)
        
        # Load danh sách nhân viên
        self.refresh_employee_list()
    
    def init_attendance_tab(self):
        # Frame chính cho tab chấm công
        main_frame = ttk.Frame(self.attendance_tab)
        main_frame.pack(fill="both", expand=True)
        
        # Frame bên trái cho camera
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        # Frame cho camera
        camera_frame = ttk.LabelFrame(left_frame, text="Camera")
        camera_frame.pack(fill="both", expand=True)
        
        self.attendance_camera_label = ttk.Label(camera_frame)
        self.attendance_camera_label.pack(padx=5, pady=5)
        
        # Frame cho nút điều khiển camera
        camera_control_frame = ttk.Frame(camera_frame)
        camera_control_frame.pack(padx=5, pady=5)
        
        self.attendance_start_btn = ttk.Button(camera_control_frame, text="Bắt đầu nhận diện", 
                                             command=self.toggle_attendance_camera)
        self.attendance_start_btn.pack(side="left", padx=5)
        
        # Label hiển thị trạng thái
        self.status_label = ttk.Label(camera_frame, text="Trạng thái: Chưa nhận diện")
        self.status_label.pack(padx=5, pady=5)
        
        # Frame bên phải cho danh sách chấm công
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)
        
        # Frame cho danh sách chấm công
        attendance_list_frame = ttk.LabelFrame(right_frame, text="Lịch sử chấm công")
        attendance_list_frame.pack(fill="both", expand=True)
        
        # Frame cho nút làm mới
        refresh_frame = ttk.Frame(attendance_list_frame)
        refresh_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(refresh_frame, text="Làm mới", 
                  command=self.refresh_attendance_list).pack(side="left", padx=5)
        
        # Treeview cho danh sách chấm công
        columns = ("ID", "Tên", "Check-in", "Check-out")
        self.attendance_tree = ttk.Treeview(attendance_list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.attendance_tree.heading(col, text=col)
            self.attendance_tree.column(col, width=100)
        
        self.attendance_tree.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(attendance_list_frame, orient="vertical", 
                                 command=self.attendance_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.attendance_tree.configure(yscrollcommand=scrollbar.set)
        
        # Load danh sách chấm công
        self.refresh_attendance_list()
        
        # Biến lưu thông tin người dùng hiện tại
        self.current_user = None
        self.last_recognition_time = {}  # Thêm biến để theo dõi thời gian nhận diện cuối cùng
    
    def toggle_camera(self):
        if self.is_capturing:
            self.is_capturing = False
            self.start_camera_btn.configure(text="Bắt đầu camera")
            self.capture_btn.configure(state="disabled")
            if self.cap is not None:
                self.cap.release()
        else:
            self.cap = cv2.VideoCapture(0)
            self.is_capturing = True
            self.start_camera_btn.configure(text="Dừng camera")
            self.capture_btn.configure(state="normal")
            self.update_camera()
    
    def toggle_attendance_camera(self):
        if self.is_capturing:
            self.is_capturing = False
            self.attendance_start_btn.configure(text="Bắt đầu nhận diện")
            self.status_label.configure(text="Trạng thái: Đã dừng")
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                # Xóa hình ảnh camera
                self.attendance_camera_label.configure(image='')
        else:
            self.cap = cv2.VideoCapture(0)
            self.is_capturing = True
            self.attendance_start_btn.configure(text="Dừng nhận diện")
            self.status_label.configure(text="Trạng thái: Đang nhận diện...")
            self.update_attendance_camera()
    
    def update_camera(self):
        if self.is_capturing:
            ret, frame = self.cap.read()
            if ret:
                # Chuyển đổi frame từ BGR sang RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Resize frame
                frame = cv2.resize(frame, (640, 480))
                # Chuyển đổi frame thành PhotoImage
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image=image)
                # Cập nhật label
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo
                # Lưu frame hiện tại
                self.current_frame = frame
            # Lặp lại sau 10ms
            self.root.after(10, self.update_camera)
    
    def update_attendance_camera(self):
        if self.is_capturing:
            ret, frame = self.cap.read()
            if ret:
                # Chuyển đổi frame từ BGR sang RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Resize frame
                frame = cv2.resize(frame, (640, 480))
                
                # Thực hiện nhận diện khuôn mặt
                self.recognize_face(frame)
                
                # Chuyển đổi frame thành PhotoImage
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image=image)
                # Cập nhật label
                self.attendance_camera_label.configure(image=photo)
                self.attendance_camera_label.image = photo
                
            # Lặp lại sau 10ms
            self.root.after(10, self.update_attendance_camera)
    
    def capture_face(self):
        if self.current_frame is not None:
            # Tạo thư mục nếu chưa tồn tại
            if not os.path.exists("face_dataset"):
                os.makedirs("face_dataset")
            
            # Lưu ảnh
            name = self.name_entry.get()
            if name:
                face_dir = os.path.join("face_dataset", name)
                if not os.path.exists(face_dir):
                    os.makedirs(face_dir)
                
                # Lưu ảnh với timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = os.path.join(face_dir, f"{name}_{timestamp}.jpg")
                cv2.imwrite(image_path, cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR))
                
                messagebox.showinfo("Thành công", "Đã lưu ảnh khuôn mặt!")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập tên nhân viên!")
    
    def recognize_face(self, frame):
        try:
            # Chuyển frame sang grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Phát hiện khuôn mặt
            faces = self.face_detector.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                # Cắt khuôn mặt
                face_roi = gray[y:y+h, x:x+w]
                
                try:
                    # Resize về kích thước 200x200
                    face_roi = cv2.resize(face_roi, (200, 200))
                    
                    # Dự đoán ID và độ tin cậy
                    id, confidence = self.face_recognizer.predict(face_roi)
                    
                    # Vẽ hình chữ nhật xung quanh khuôn mặt
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Nếu độ tin cậy < 50, xem như nhận diện thành công
                    if confidence < 50:
                        # Tìm tên từ ID
                        name = next((name for name, id_num in self.names.items() if id_num == id), "Unknown")
                        
                        # Hiển thị tên và độ tin cậy
                        text = f"{name} ({confidence:.2f}%)"
                        cv2.putText(frame, text, (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                        
                        # Kiểm tra thời gian từ lần nhận diện cuối
                        current_time = datetime.now()
                        if name not in self.last_recognition_time or \
                           (current_time - self.last_recognition_time[name]).total_seconds() > 5:
                            # Tự động xử lý check-in/out
                            self.process_attendance(name, "auto")
                            self.last_recognition_time[name] = current_time
                            
                        self.status_label.configure(text=f"Trạng thái: Đã nhận diện {name}")
                    else:
                        cv2.putText(frame, "Unknown", (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                        self.status_label.configure(text="Trạng thái: Chưa nhận diện được")
                        
                except Exception as e:
                    print(f"Lỗi khi xử lý khuôn mặt: {e}")
                    continue
                    
        except Exception as e:
            print(f"Lỗi khi nhận diện khuôn mặt: {e}")
    
    def process_attendance(self, name, action="auto"):
        try:
            # Lấy ID nhân viên từ tên
            self.cursor.execute('SELECT id FROM employees WHERE name = ?', (name,))
            result = self.cursor.fetchone()
            
            if result:
                employee_id = result[0]
                current_time = datetime.now()
                
                # Kiểm tra trạng thái check-in/out hiện tại
                self.cursor.execute('''
                    SELECT id, check_in, check_out 
                    FROM attendance 
                    WHERE employee_id = ? 
                    ORDER BY check_in DESC LIMIT 1
                ''', (employee_id,))
                last_record = self.cursor.fetchone()
                
                if not last_record or last_record[2] is not None:  # Chưa có bản ghi hoặc đã check-out
                    # Check-in
                    self.cursor.execute('''
                        INSERT INTO attendance (employee_id, check_in)
                        VALUES (?, ?)
                    ''', (employee_id, current_time))
                    self.conn.commit()
                    messagebox.showinfo("Thông báo", f"{name} đã check-in!")
                    self.status_label.configure(text=f"Trạng thái: {name} đã check-in")
                else:  # Đã check-in nhưng chưa check-out
                    # Check-out
                    self.cursor.execute('''
                        UPDATE attendance 
                        SET check_out = ?
                        WHERE id = ?
                    ''', (current_time, last_record[0]))
                    self.conn.commit()
                    messagebox.showinfo("Thông báo", f"{name} đã check-out!")
                    self.status_label.configure(text=f"Trạng thái: {name} đã check-out")
                
                # Cập nhật danh sách chấm công
                self.refresh_attendance_list()
                
                # Dừng camera sau khi xử lý xong
                self.toggle_attendance_camera()
                
        except sqlite3.Error as e:
            print(f"Lỗi khi xử lý chấm công: {e}")
            messagebox.showerror("Lỗi", f"Không thể xử lý chấm công: {str(e)}")
    
    def add_employee(self):
        name = self.name_entry.get()
        position = self.position_entry.get()
        department = self.department_entry.get()
        
        if name:
            try:
                self.cursor.execute('''
                    INSERT INTO employees (name, position, department)
                    VALUES (?, ?, ?)
                ''', (name, position, department))
                self.conn.commit()
                self.refresh_employee_list()
                self.clear_entries()
                messagebox.showinfo("Thành công", "Đã thêm nhân viên mới!")
            except sqlite3.Error as e:
                messagebox.showerror("Lỗi", f"Không thể thêm nhân viên: {str(e)}")
        else:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên nhân viên!")
    
    def edit_employee(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item[0])
            employee_id = item['values'][0]
            
            # Tạo cửa sổ mới để sửa thông tin
            edit_window = tk.Toplevel(self.root)
            edit_window.title("Sửa thông tin nhân viên")
            edit_window.geometry("300x200")
            
            # Các trường nhập liệu
            ttk.Label(edit_window, text="Tên:").pack(padx=5, pady=5)
            name_entry = ttk.Entry(edit_window)
            name_entry.insert(0, item['values'][1])
            name_entry.pack(padx=5, pady=5)
            
            ttk.Label(edit_window, text="Chức vụ:").pack(padx=5, pady=5)
            position_entry = ttk.Entry(edit_window)
            position_entry.insert(0, item['values'][2])
            position_entry.pack(padx=5, pady=5)
            
            ttk.Label(edit_window, text="Phòng ban:").pack(padx=5, pady=5)
            department_entry = ttk.Entry(edit_window)
            department_entry.insert(0, item['values'][3])
            department_entry.pack(padx=5, pady=5)
            
            def save_changes():
                try:
                    self.cursor.execute('''
                        UPDATE employees
                        SET name=?, position=?, department=?
                        WHERE id=?
                    ''', (name_entry.get(), position_entry.get(), 
                         department_entry.get(), employee_id))
                    self.conn.commit()
                    self.refresh_employee_list()
                    edit_window.destroy()
                    messagebox.showinfo("Thành công", "Đã cập nhật thông tin!")
                except sqlite3.Error as e:
                    messagebox.showerror("Lỗi", f"Không thể cập nhật: {str(e)}")
            
            ttk.Button(edit_window, text="Lưu", command=save_changes).pack(padx=5, pady=5)
        else:
            messagebox.showerror("Lỗi", "Vui lòng chọn nhân viên cần sửa!")
    
    def delete_employee(self):
        selected_item = self.tree.selection()
        if selected_item:
            if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa nhân viên này?"):
                employee_id = self.tree.item(selected_item[0])['values'][0]
                try:
                    self.cursor.execute('DELETE FROM employees WHERE id=?', (employee_id,))
                    self.conn.commit()
                    self.refresh_employee_list()
                    messagebox.showinfo("Thành công", "Đã xóa nhân viên!")
                except sqlite3.Error as e:
                    messagebox.showerror("Lỗi", f"Không thể xóa: {str(e)}")
        else:
            messagebox.showerror("Lỗi", "Vui lòng chọn nhân viên cần xóa!")
    
    def refresh_employee_list(self):
        # Xóa tất cả items hiện tại
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load lại danh sách từ database
        self.cursor.execute('SELECT * FROM employees')
        for row in self.cursor.fetchall():
            self.tree.insert('', 'end', values=row)
    
    def refresh_attendance_list(self):
        # Xóa tất cả items hiện tại
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
        
        # Load lại danh sách từ database
        self.cursor.execute('''
            SELECT a.id, e.name, a.check_in, a.check_out
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            ORDER BY a.check_in DESC
        ''')
        for row in self.cursor.fetchall():
            self.attendance_tree.insert('', 'end', values=row)
    
    def clear_entries(self):
        self.name_entry.delete(0, 'end')
        self.position_entry.delete(0, 'end')
        self.department_entry.delete(0, 'end')
    
    def view_employee_history(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn nhân viên để xem lịch sử!")
            return
            
        employee_id = self.tree.item(selected_item[0])['values'][0]
        employee_name = self.tree.item(selected_item[0])['values'][1]
        
        # Tạo cửa sổ mới để hiển thị lịch sử
        history_window = tk.Toplevel(self.root)
        history_window.title(f"Lịch sử chấm công - {employee_name}")
        history_window.geometry("1000x600")
        
        # Frame cho bộ lọc
        filter_frame = ttk.Frame(history_window)
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Từ ngày:").pack(side="left", padx=5)
        from_date = ttk.Entry(filter_frame, width=10)
        from_date.pack(side="left", padx=5)
        from_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(filter_frame, text="Đến ngày:").pack(side="left", padx=5)
        to_date = ttk.Entry(filter_frame, width=10)
        to_date.pack(side="left", padx=5)
        to_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        def apply_filter():
            try:
                from_dt = datetime.strptime(from_date.get(), "%Y-%m-%d")
                to_dt = datetime.strptime(to_date.get(), "%Y-%m-%d")
                to_dt = to_dt.replace(hour=23, minute=59, second=59)
                
                # Xóa dữ liệu cũ
                for item in history_tree.get_children():
                    history_tree.delete(item)
                
                # Lấy dữ liệu mới
                self.cursor.execute('''
                    SELECT id, check_in, check_out,
                           ROUND((julianday(check_out) - julianday(check_in)) * 24, 2) as hours
                    FROM attendance 
                    WHERE employee_id = ? 
                    AND check_in >= ?
                    AND check_in <= ?
                    ORDER BY check_in DESC
                ''', (employee_id, from_dt, to_dt))
                
                for row in self.cursor.fetchall():
                    check_in = row[1].strftime("%Y-%m-%d %H:%M:%S") if row[1] else ""
                    check_out = row[2].strftime("%Y-%m-%d %H:%M:%S") if row[2] else ""
                    hours = f"{row[3]:.2f}" if row[3] else ""
                    history_tree.insert('', 'end', values=(row[0], check_in, check_out, hours))
                    
            except ValueError:
                messagebox.showerror("Lỗi", "Định dạng ngày không hợp lệ! Sử dụng YYYY-MM-DD")
        
        ttk.Button(filter_frame, text="Lọc", command=apply_filter).pack(side="left", padx=5)
        
        # Frame cho CRUD buttons
        crud_frame = ttk.Frame(history_window)
        crud_frame.pack(fill="x", padx=5, pady=5)
        
        def edit_record():
            selected = history_tree.selection()
            if not selected:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn bản ghi cần sửa!")
                return
                
            record_id = history_tree.item(selected[0])['values'][0]
            check_in = history_tree.item(selected[0])['values'][1]
            check_out = history_tree.item(selected[0])['values'][2]
            
            # Tạo cửa sổ sửa
            edit_window = tk.Toplevel(history_window)
            edit_window.title("Sửa thời gian chấm công")
            edit_window.geometry("300x200")
            
            ttk.Label(edit_window, text="Check-in:").pack(padx=5, pady=5)
            check_in_entry = ttk.Entry(edit_window)
            check_in_entry.insert(0, check_in)
            check_in_entry.pack(padx=5, pady=5)
            
            ttk.Label(edit_window, text="Check-out:").pack(padx=5, pady=5)
            check_out_entry = ttk.Entry(edit_window)
            check_out_entry.insert(0, check_out)
            check_out_entry.pack(padx=5, pady=5)
            
            def save_changes():
                try:
                    new_check_in = datetime.strptime(check_in_entry.get(), "%Y-%m-%d %H:%M:%S")
                    new_check_out = datetime.strptime(check_out_entry.get(), "%Y-%m-%d %H:%M:%S") if check_out_entry.get() else None
                    
                    self.cursor.execute('''
                        UPDATE attendance 
                        SET check_in = ?, check_out = ?
                        WHERE id = ?
                    ''', (new_check_in, new_check_out, record_id))
                    self.conn.commit()
                    
                    messagebox.showinfo("Thành công", "Đã cập nhật thời gian chấm công!")
                    edit_window.destroy()
                    apply_filter()  # Cập nhật lại danh sách
                    
                except ValueError:
                    messagebox.showerror("Lỗi", "Định dạng thời gian không hợp lệ!")
                except sqlite3.Error as e:
                    messagebox.showerror("Lỗi", f"Không thể cập nhật: {str(e)}")
            
            ttk.Button(edit_window, text="Lưu", command=save_changes).pack(padx=5, pady=5)
        
        def delete_record():
            selected = history_tree.selection()
            if not selected:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn bản ghi cần xóa!")
                return
                
            if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa bản ghi này?"):
                record_id = history_tree.item(selected[0])['values'][0]
                try:
                    self.cursor.execute('DELETE FROM attendance WHERE id = ?', (record_id,))
                    self.conn.commit()
                    messagebox.showinfo("Thành công", "Đã xóa bản ghi!")
                    apply_filter()  # Cập nhật lại danh sách
                except sqlite3.Error as e:
                    messagebox.showerror("Lỗi", f"Không thể xóa: {str(e)}")
        
        def add_record():
            # Tạo cửa sổ thêm mới
            add_window = tk.Toplevel(history_window)
            add_window.title("Thêm bản ghi chấm công")
            add_window.geometry("300x200")
            
            ttk.Label(add_window, text="Check-in:").pack(padx=5, pady=5)
            check_in_entry = ttk.Entry(add_window)
            check_in_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            check_in_entry.pack(padx=5, pady=5)
            
            ttk.Label(add_window, text="Check-out:").pack(padx=5, pady=5)
            check_out_entry = ttk.Entry(add_window)
            check_out_entry.pack(padx=5, pady=5)
            
            def save_new():
                try:
                    new_check_in = datetime.strptime(check_in_entry.get(), "%Y-%m-%d %H:%M:%S")
                    new_check_out = datetime.strptime(check_out_entry.get(), "%Y-%m-%d %H:%M:%S") if check_out_entry.get() else None
                    
                    self.cursor.execute('''
                        INSERT INTO attendance (employee_id, check_in, check_out)
                        VALUES (?, ?, ?)
                    ''', (employee_id, new_check_in, new_check_out))
                    self.conn.commit()
                    
                    messagebox.showinfo("Thành công", "Đã thêm bản ghi mới!")
                    add_window.destroy()
                    apply_filter()  # Cập nhật lại danh sách
                    
                except ValueError:
                    messagebox.showerror("Lỗi", "Định dạng thời gian không hợp lệ!")
                except sqlite3.Error as e:
                    messagebox.showerror("Lỗi", f"Không thể thêm mới: {str(e)}")
            
            ttk.Button(add_window, text="Thêm", command=save_new).pack(padx=5, pady=5)
        
        ttk.Button(crud_frame, text="Thêm mới", command=add_record).pack(side="left", padx=5)
        ttk.Button(crud_frame, text="Sửa", command=edit_record).pack(side="left", padx=5)
        ttk.Button(crud_frame, text="Xóa", command=delete_record).pack(side="left", padx=5)
        
        # Treeview cho lịch sử
        history_frame = ttk.Frame(history_window)
        history_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        columns = ("ID", "Check-in", "Check-out", "Số giờ")
        history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        
        for col in columns:
            history_tree.heading(col, text=col)
            history_tree.column(col, width=200)
        
        history_tree.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=history_tree.yview)
        scrollbar.pack(side="right", fill="y")
        history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Áp dụng bộ lọc ban đầu
        apply_filter()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AttendanceSystem()
    app.run() 