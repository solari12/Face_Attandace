import cv2
import os

def collect_faces():
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists("face_dataset"):
        os.makedirs("face_dataset")
    
    face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    def face_cropped(img):
        if img is None:
            return None
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_classifier.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                return None
                
            for (x,y,w,h) in faces:
                cropped_face = img[y:y+h, x:x+w]
            return cropped_face
        except Exception as e:
            print(f"Lỗi khi xử lý ảnh: {e}")
            return None
    
    # Thử các camera index khác nhau
    for camera_index in [0, 1]:
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            print(f"Đã kết nối với camera {camera_index}")
            break
    else:
        print("Không tìm thấy camera nào!")
        return
    
    # Hiển thị danh sách người dùng hiện tại
    print("\nDanh sách người dùng hiện tại:")
    for person_name in os.listdir("face_dataset"):
        if os.path.isdir(os.path.join("face_dataset", person_name)):
            print(f"Tên: {person_name}")
    
    # Nhập thông tin người dùng mới
    name = input("\nNhập tên người dùng mới: ")
    user_dir = os.path.join("face_dataset", name)
    
    if os.path.exists(user_dir):
        print(f"Người dùng '{name}' đã tồn tại!")
        return
    
    # Tạo thư mục cho người dùng mới
    os.makedirs(user_dir)
    print(f"\nĐã tạo người dùng mới - Tên: {name}")
    
    img_id = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không thể đọc frame từ camera")
            break
            
        # Hiển thị frame gốc
        cv2.imshow("Camera", frame)
        
        if face_cropped(frame) is not None:
            img_id += 1
            face = cv2.resize(face_cropped(frame), (200,200))
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
            file_name_path = os.path.join(user_dir, f"{name}_{img_id}.png")
            cv2.imwrite(file_name_path, face)
            cv2.putText(face, str(img_id), (50,50), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 2)
            
            cv2.imshow("Cropped face", face)
            print(f"Đã lưu ảnh {img_id}")
        
        # Nhấn Enter để thoát hoặc đủ 200 ảnh
        if cv2.waitKey(1) == 13 or img_id >= 200:
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Hoàn thành thu thập dữ liệu!")

if __name__ == "__main__":
    collect_faces() 