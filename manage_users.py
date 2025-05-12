import os
import pickle
import shutil
import cv2
from PIL import Image
import numpy as np

def reindex_users(user_info):
    # Tạo dictionary mới với ID được đánh lại từ 1
    new_users = {}
    for i, (old_id, name) in enumerate(user_info["users"].items(), 1):
        new_users[i] = name
    
    # Cập nhật user_info
    user_info["users"] = new_users
    user_info["next_id"] = len(new_users) + 1
    
    # Đổi tên các file ảnh
    if os.path.exists("data"):
        for old_id, new_id in zip(sorted(user_info["users"].keys()), range(1, len(user_info["users"]) + 1)):
            for file in os.listdir("data"):
                if file.startswith(f"person.{old_id}."):
                    new_file = file.replace(f"person.{old_id}.", f"person.{new_id}.")
                    os.rename(os.path.join("data", file), os.path.join("data", new_file))
    
    return user_info

def train_classifier(data_dir):
    # Lấy danh sách đường dẫn của tất cả ảnh trong thư mục data_dir
    path = [os.path.join(data_dir, f) for f in os.listdir(data_dir)]
    
    faces = []  # Lưu các ảnh khuôn mặt
    ids = []    # Lưu ID tương ứng với mỗi khuôn mặt
    
    # Xử lý từng ảnh
    for image in path:
        # Mở ảnh và chuyển sang grayscale
        img = Image.open(image).convert('L')
        # Chuyển ảnh thành mảng numpy
        imageNp = np.array(img, 'uint8')
        # Lấy ID từ tên file (giả sử tên file có format: person.1.jpg)
        id = int(os.path.split(image)[1].split(".")[1])
        
        faces.append(imageNp)
        ids.append(id)
    
    # Chuyển ids thành mảng numpy
    ids = np.array(ids)
    
    # Tạo và huấn luyện mô hình LBPH
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, ids)
    # Lưu mô hình đã huấn luyện vào file classifier.xml
    clf.write("classifier.xml")
    print("Đã huấn luyện lại mô hình thành công!")

def manage_users():
    # Tải thông tin người dùng
    if not os.path.exists("user_info.pkl"):
        print("Chưa có thông tin người dùng nào!")
        return
        
    with open("user_info.pkl", "rb") as f:
        user_info = pickle.load(f)
    
    while True:
        print("\n=== QUẢN LÝ NGƯỜI DÙNG ===")
        print("1. Xem danh sách người dùng")
        print("2. Xóa người dùng")
        print("3. Thoát")
        
        choice = input("\nChọn chức năng (1-3): ")
        
        if choice == "1":
            print("\nDanh sách người dùng:")
            for user_id, name in user_info["users"].items():
                print(f"ID: {user_id}, Tên: {name}")
                
        elif choice == "2":
            print("\nDanh sách người dùng:")
            for user_id, name in user_info["users"].items():
                print(f"ID: {user_id}, Tên: {name}")
            
            try:
                delete_id = int(input("\nNhập ID của người dùng cần xóa: "))
                if delete_id in user_info["users"]:
                    # Xác nhận xóa
                    confirm = input(f"Bạn có chắc muốn xóa người dùng {user_info['users'][delete_id]} (ID: {delete_id})? (y/n): ")
                    if confirm.lower() == 'y':
                        # Xóa thông tin người dùng
                        del user_info["users"][delete_id]
                        
                        # Xóa ảnh của người dùng
                        for file in os.listdir("data"):
                            if file.startswith(f"person.{delete_id}."):
                                os.remove(os.path.join("data", file))
                        
                        # Cập nhật lại ID
                        user_info = reindex_users(user_info)
                        
                        # Lưu lại thông tin
                        with open("user_info.pkl", "wb") as f:
                            pickle.dump(user_info, f)
                            
                        print("Đã xóa người dùng và cập nhật lại ID thành công!")
                        
                        # Huấn luyện lại mô hình
                        if os.path.exists("data") and len(os.listdir("data")) > 0:
                            print("Đang huấn luyện lại mô hình...")
                            train_classifier("data")
                        else:
                            print("Không còn dữ liệu để huấn luyện mô hình!")
                    else:
                        print("Đã hủy xóa!")
                else:
                    print("Không tìm thấy ID này!")
            except ValueError:
                print("ID không hợp lệ!")
                
        elif choice == "3":
            break
            
        else:
            print("Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    manage_users() 