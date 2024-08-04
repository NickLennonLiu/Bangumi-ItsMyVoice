import os
import numpy as np
import librosa
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import shutil

def extract_features(file_name):
    y, sr = librosa.load(file_name, sr=None)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfccs_mean = np.mean(mfccs, axis=1)
    return mfccs_mean

def load_audio_files(folder_path):
    features = []
    file_names = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".wav"):
            file_path = os.path.join(folder_path, file_name)
            mfccs = extract_features(file_path)
            features.append(mfccs)
            file_names.append(file_name)
    return np.array(features), file_names

def perform_clustering(features, n_clusters):
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    kmeans = KMeans(n_clusters=n_clusters, random_state=0)
    kmeans.fit(scaled_features)
    return kmeans.labels_

def plot_clusters(labels, file_names):
    plt.figure(figsize=(10, 8))
    plt.scatter(range(len(labels)), labels, c=labels, cmap='viridis')
    plt.xlabel('File Index')
    plt.ylabel('Cluster Label')
    plt.title('Speaker Clustering')
    for i, txt in enumerate(file_names):
        plt.annotate(txt, (i, labels[i]), fontsize=8)
    plt.show()

def save_files_to_clusters(folder_path, file_names, labels, output_path):
    for label in set(labels):
        cluster_folder = os.path.join(output_path, f'cluster_{label}')
        os.makedirs(cluster_folder, exist_ok=True)

    for file_name, label in zip(file_names, labels):
        src_file = os.path.join(folder_path, file_name)
        dst_file = os.path.join(output_path, f'cluster_{label}', file_name)
        shutil.move(src_file, dst_file)

# 主程序
output_path = 'C:\\Users\\River\\Models\\AniVoiceDatasetPreparer\\output\\Dungeon Meshi\\cluster'  # 替换为输出文件夹路径
n_clusters = 5  # 设置聚类的数量




# 主程序
folder_path = 'C:\\Users\\River\\Models\\AniVoiceDatasetPreparer\\output\\Dungeon Meshi\\split\\01_[Nekomoe kissaten&LoliHouse] Dungeon Meshi - 01 [WebRip 1080p HEVC-10bit AAC EAC3 ASSx2]_(Vocals)'  # 替换为您的 wav 文件所在的文件夹路径
n_clusters = 5  # 设置聚类的数量


features, file_names = load_audio_files(folder_path)
labels = perform_clustering(features, n_clusters)
plot_clusters(labels, file_names)
save_files_to_clusters(folder_path, file_names, labels, output_path)