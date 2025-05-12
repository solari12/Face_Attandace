# Hệ Thống Điểm Danh Bằng Nhận Diện Khuôn Mặt

Đây là một ứng dụng điểm danh tự động sử dụng công nghệ nhận diện khuôn mặt, được phát triển bằng Python. Ứng dụng cho phép quản lý điểm danh của nhân viên một cách tự động và hiệu quả.

## Tính Năng Chính

- Nhận diện khuôn mặt tự động
- Quản lý thông tin nhân viên
- Theo dõi thời gian điểm danh
- Giao diện người dùng thân thiện
- Xuất báo cáo điểm danh
- Phân quyền người dùng (Admin và Nhân viên)

## Yêu Cầu Hệ Thống

- Python 3.8 trở lên
- Webcam hoặc camera
- Đủ dung lượng ổ cứng để lưu trữ dữ liệu khuôn mặt
- Kết nối internet (không bắt buộc)

## Cài Đặt

1. Clone repository này về máy của bạn:
```bash
git clone https://github.com/solari12/Face_Attandace.git
cd [tên thư mục]
```

2. Tạo môi trường ảo Python (khuyến nghị):
```bash
python -m venv .venv
```

3. Kích hoạt môi trường ảo:
- Windows:
```bash
.venv\Scripts\activate
```
- Linux/Mac:
```bash
source .venv/bin/activate
```

4. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Cách Sử Dụng

### 1. Khởi động ứng dụng

Chạy file main_app.py để khởi động ứng dụng:
```bash
python manager_app.py
```
### 3. Thu thập dữ liệu khuôn mặt

1. Đăng nhập với tài khoản manager_app.py
2. Thêm nhân viên cần thêm dữ liệu khuôn mặt
3. Nhập tên, chức vụ, phòng ban của nhân viên
4. Nhấn "Bắt đầu camera" và nhấn thu thập ảnh của nhân viên
5. Đảm bảo có đủ ánh sáng và ngồi đối diện camera
6. Thu thập ít nhất 100-200 ảnh khuôn mặt để có độ chính xác cao

### 4. Điểm danh

1. Đăng nhập vào hệ thống
2. Chọn chức năng "Điểm danh"
3. Ngồi đối diện camera
4. Hệ thống sẽ tự động nhận diện và ghi nhận điểm danh

### 5. Xem báo cáo

1. Nhấn vào nhân viên
2. Vào phần "Xem lịch sử"
3. Chọn khoảng thời gian cần xem
4. Xuất báo cáo nếu cần

## Cấu Trúc Thư Mục

- `manager_app.py`: Module quản lý dành cho admin
- `employee_app.py`: Module dành cho nhân viên
- `train_model.py`: Script huấn luyện model nhận diện
- `collect_faces.py`: Script thu thập dữ liệu khuôn mặt
- `recognize_face.py`: Module nhận diện khuôn mặt
- `manage_users.py`: Quản lý người dùng
- `face_dataset/`: Thư mục lưu trữ dữ liệu khuôn mặt
- `attendance.db`: Cơ sở dữ liệu SQLite

## Lưu ý Quan Trọng

1. Đảm bảo có đủ ánh sáng khi sử dụng chức năng nhận diện
2. Giữ khoảng cách phù hợp với camera (khoảng 50-100cm)
3. Không đeo kính râm hoặc vật che khuất khuôn mặt
4. Thường xuyên sao lưu dữ liệu
5. Cập nhật dữ liệu khuôn mặt định kỳ để tăng độ chính xác

## Hỗ Trợ

Nếu bạn gặp vấn đề hoặc cần hỗ trợ, vui lòng:
1. Kiểm tra các vấn đề thường gặp trong phần FAQ
2. Tạo issue mới trên repository
3. Liên hệ với đội ngũ phát triển

## Giấy Phép

[MIT License](LICENSE)
