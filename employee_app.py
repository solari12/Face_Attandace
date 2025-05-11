import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import os
from datetime import datetime
import sqlite3
from PIL import Image, ImageTk
import pickle

# Đăng ký adapter cho datetime
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(s):
    return datetime.fromisoformat(s.decode())

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("datetime", convert_datetime)

class EmployeeSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hệ thống chấm công")
        self.root.geometry("1200x700")
        
        # Khởi tạo database với datetime converter
        self.conn = sqlite3.connect('attendance.db', detect_types=sqlite3.PARSE_DECLTYPES)
        self.cursor = self.conn.cursor()
        
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
        
        # Biến cho camera
        self.cap = None
        self.is_capturing = False
        self.current_frame = None
        
        # Biến lưu thông tin người dùng hiện tại
        self.current_user = None
        self.last_recognition_time = {}  # Thêm biến để theo dõi thời gian nhận diện cuối cùng
        
        # Khởi tạo giao diện
        self.init_attendance_tab()
        
    def init_attendance_tab(self):
        # Frame chính cho tab chấm công
        main_frame = ttk.Frame(self.root)
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
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = EmployeeSystem()
    app.run() 