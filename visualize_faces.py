import os
import cv2
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Sử dụng backend TkAgg
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import seaborn as sns

def load_face_images(data_dir="face_dataset"):
    person_faces = {}  # Dictionary để lưu tất cả ảnh của mỗi người
    all_faces = []     # List để lưu tất cả ảnh riêng lẻ
    all_labels = []    # List để lưu nhãn của từng ảnh
    
    # Duyệt qua tất cả các thư mục con
    for person_dir in os.listdir(data_dir):
        person_path = os.path.join(data_dir, person_dir)
        if not os.path.isdir(person_path):
            continue
            
        faces = []
        # Duyệt qua tất cả ảnh trong thư mục của người đó
        for image_file in os.listdir(person_path):
            if not image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            image_path = os.path.join(person_path, image_file)
            try:
                # Đọc và resize ảnh
                img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                img = cv2.resize(img, (200, 200))
                face_vector = img.flatten()  # Chuyển ảnh thành vector 1D
                
                faces.append(face_vector)
                all_faces.append(face_vector)
                all_labels.append(person_dir)
            except Exception as e:
                print(f"Lỗi khi xử lý {image_path}: {str(e)}")
                continue
        
        if faces:  # Nếu có ảnh hợp lệ
            # Tính trung bình các ảnh của người này
            person_faces[person_dir] = np.mean(faces, axis=0)
    
    return person_faces, np.array(all_faces), all_labels

def visualize_face_similarities():
    try:
        # Load dữ liệu
        person_faces, all_faces, all_labels = load_face_images()
        if not person_faces:
            print("Không tìm thấy ảnh khuôn mặt nào!")
            return
        
        # Chuyển dictionary thành array và lấy tên người
        faces_array = np.array(list(person_faces.values()))
        person_names = list(person_faces.keys())
        
        # Tính ma trận tương đồng giữa các người
        similarity_matrix = cosine_similarity(faces_array)
        
        # Tạo figure với 2 subplot
        plt.figure(figsize=(15, 6))
        
        # 1. Heatmap của ma trận tương đồng (chỉ giữa các người)
        plt.subplot(1, 2, 1)
        sns.heatmap(similarity_matrix, 
                    xticklabels=person_names,
                    yticklabels=person_names,
                    cmap='viridis',
                    annot=True,  # Hiển thị giá trị
                    fmt='.2f')   # Format số thập phân
        plt.title('Ma trận tương đồng giữa các người dùng')
        plt.xlabel('Người dùng')
        plt.ylabel('Người dùng')
        
        # 2. PCA visualization với tất cả ảnh
        pca = PCA(n_components=2)
        faces_2d = pca.fit_transform(all_faces)
        
        # Áp dụng K-means với số cluster bằng số người
        n_clusters = len(person_names)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(faces_2d)
        
        plt.subplot(1, 2, 2)
        
        # Tạo mesh grid với kích thước nhỏ hơn
        x_min, x_max = faces_2d[:, 0].min() - 1, faces_2d[:, 0].max() + 1
        y_min, y_max = faces_2d[:, 1].min() - 1, faces_2d[:, 1].max() + 1
        
        # Tính toán step size dựa trên phạm vi dữ liệu
        x_range = x_max - x_min
        y_range = y_max - y_min
        step = max(x_range, y_range) / 100  # Chia thành 100 phần
        
        xx, yy = np.meshgrid(np.arange(x_min, x_max, step),
                            np.arange(y_min, y_max, step))
        
        # Dự đoán nhãn cho mỗi điểm trong mesh grid
        Z = kmeans.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)
        
        # Vẽ các vùng màu
        plt.contourf(xx, yy, Z, alpha=0.3, cmap='viridis')
        
        # Vẽ tất cả các điểm với màu theo cluster
        scatter = plt.scatter(faces_2d[:, 0], faces_2d[:, 1], c=clusters, 
                            cmap='viridis', alpha=0.6, edgecolors='black')
        
        # Tính và vẽ trung tâm của mỗi cluster
        centers = kmeans.cluster_centers_
        plt.scatter(centers[:, 0], centers[:, 1], c='red', marker='x', 
                   s=200, linewidths=3, label='Cluster Centers')
        
        # Thêm tên người vào các trung tâm cluster
        for i, name in enumerate(person_names):
            plt.annotate(name, (centers[i, 0], centers[i, 1]), 
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5))
        
        plt.title('Phân cụm tất cả ảnh khuôn mặt (PCA + K-means)')
        plt.xlabel('Principal Component 1')
        plt.ylabel('Principal Component 2')
        
        # Thêm thông tin về variance explained
        variance_ratio = pca.explained_variance_ratio_
        plt.figtext(0.5, 0.01, 
                    f'Variance explained: PC1={variance_ratio[0]:.2%}, PC2={variance_ratio[1]:.2%}',
                    ha='center')
        
        plt.tight_layout()
        
        # Lưu ảnh trước khi hiển thị
        plt.savefig('face_visualization.png')
        
        # Hiển thị plot
        plt.show()
        
    except Exception as e:
        print(f"Có lỗi xảy ra: {str(e)}")
        print("Đã lưu kết quả vào file 'face_visualization.png'")

if __name__ == "__main__":
    visualize_face_similarities() 