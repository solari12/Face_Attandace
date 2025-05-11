import os
import cv2
from PIL import Image
import numpy as np
import pickle

def train_classifier(data_dir):
    faces = []  # Lưu các ảnh khuôn mặt
    ids = []    # Lưu ID tương ứng với mỗi khuôn mặt
    names = {}  # Dictionary để lưu mapping giữa ID và tên
    
    # Duyệt qua tất cả các thư mục con
    for person_dir in os.listdir(data_dir):
        person_path = os.path.join(data_dir, person_dir)
        if not os.path.isdir(person_path):
            continue
            
        # Lấy tên người từ tên thư mục
        name = person_dir
        
        # Tạo ID số cho tên nếu chưa có
        if name not in names:
            names[name] = len(names) + 1
            
        # Duyệt qua tất cả ảnh trong thư mục của người đó
        for image_file in os.listdir(person_path):
            if not image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            image_path = os.path.join(person_path, image_file)
            try:
                # Mở ảnh và chuyển sang grayscale
                img = Image.open(image_path).convert('L')
                # Chuyển ảnh thành mảng numpy
                imageNp = np.array(img, 'uint8')
                
                faces.append(imageNp)
                ids.append(names[name])
            except Exception as e:
                print(f"Error processing {image_path}: {str(e)}")
                continue
    
    if not faces:
        print("No valid images found in the dataset!")
        return
        
    # Lưu mapping giữa ID và tên
    with open('names.pkl', 'wb') as f:
        pickle.dump(names, f)
    
    # Chuyển ids thành mảng numpy
    ids = np.array(ids)
    
    # Tạo và huấn luyện mô hình LBPH
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, ids)
    # Lưu mô hình đã huấn luyện vào file classifier.xml
    clf.write("classifier.xml")
    print("Đã huấn luyện và lưu mô hình thành công!")
    print("Danh sách người dùng:", names)

if __name__ == "__main__":
    train_classifier("face_dataset")