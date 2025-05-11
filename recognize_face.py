import cv2
import numpy as np
import pickle

def recognize_face():
    # Tải thông tin người dùng
    with open("names.pkl", "rb") as f:
        names = pickle.load(f)
    
    # Tải mô hình đã huấn luyện
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("classifier.xml")
    
    # Tải Haar Cascade cho phát hiện khuôn mặt
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Kết nối camera
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không thể đọc frame từ camera")
            break
            
        # Chuyển sang grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Phát hiện khuôn mặt
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            # Cắt khuôn mặt
            face_roi = gray[y:y+h, x:x+w]
            
            try:
                # Resize về kích thước 200x200
                face_roi = cv2.resize(face_roi, (200, 200))
                
                # Dự đoán ID
                id, confidence = clf.predict(face_roi)
                
                # Vẽ hình chữ nhật xung quanh khuôn mặt
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Hiển thị ID, tên và độ tin cậy
                if confidence < 50:
                    # Tìm tên từ ID
                    name = next((name for name, id_num in names.items() if id_num == id), "Unknown")
                    text = f"{name} ({confidence:.2f}%)"
                    cv2.putText(frame, text, (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "Unknown", (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                    
            except Exception as e:
                print(f"Lỗi khi xử lý khuôn mặt: {e}")
        
        # Hiển thị kết quả
        cv2.imshow('Face Recognition', frame)
        
        # Nhấn 'q' để thoát
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    recognize_face() 