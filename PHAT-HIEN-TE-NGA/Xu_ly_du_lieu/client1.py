import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, StandardScaler
from imblearn.over_sampling import SMOTE

# 1. Đọc dữ liệu từ file CSV
file_path = "F:/orb/Bai tap on luyen/PHAT-HIEN-TE-NGA_1-main/PHAT-HIEN-TE-NGA/Xu_ly_du_lieu/data_action.csv"
data = pd.read_csv(file_path)

# 2. Lọc các hoạt động hợp lệ(chỉ giữ lại các nhãn như ngã về các hướng và đứng bình thường).
valid_activities = ["fall_forward", "fall_backward", "fall_left", "fall_right", "standing"]
data = data[data["ActivityLabel"].isin(valid_activities)]

# 3. Chuẩn hóa dữ liệu (bỏ cột 'Time' vì không cần thiết)
features = ["AccelX", "AccelY", "AccelZ", "GyroX", "GyroY", "GyroZ"]
scaler = StandardScaler()
data[features] = scaler.fit_transform(data[features])

# 4. Mã hóa nhãn hoạt động
label_encoder = LabelEncoder()
data["ActivityLabel"] = label_encoder.fit_transform(data["ActivityLabel"])

# 5. Tạo cửa sổ trượt (Sliding Window)
window_size = 50
step_size = 25

X_windows = []
y_labels = []

for i in range(0, len(data) - window_size, step_size):
    window = data.iloc[i:i + window_size][features].values  # Chỉ lấy dữ liệu cảm biến
    label = data.iloc[i + window_size - 1]["ActivityLabel"]  # Nhãn của mẫu cuối trong cửa sổ
    X_windows.append(window)
    y_labels.append(label)

X = np.array(X_windows)  # Shape: (num_windows, 50, 6)
y = np.array(y_labels)   # Shape: (num_windows,)

# 6. Xử lý mất cân bằng dữ liệu (SMOTE)
smote = SMOTE(sampling_strategy="auto", random_state=42)
X_flat = X.reshape(X.shape[0], -1)  # Reshape để fit_resample
X_resampled, y_resampled = smote.fit_resample(X_flat, y)
X_resampled = X_resampled.reshape(-1, 50, 6)  # Đưa về dạng ban đầu

# 7. Lưu dữ liệu đã cân bằng
save_path = "F:/DATN/"
np.save(save_path + "X_balanced1.npy", X_resampled)
np.save(save_path + "y_balanced1.npy", y_resampled)

print(f"Số lượng cửa sổ sau khi cân bằng: {len(X_resampled)}")
print(f"Shape của X: {X_resampled.shape}")
print(f"Shape của y: {y_resampled.shape}")

# 8. Kiểm tra số lượng mẫu theo từng nhãn sau khi cân bằng
plt.figure(figsize=(8, 5))
activity_counts = pd.Series(y_resampled).value_counts()
activity_names = label_encoder.inverse_transform(activity_counts.index.astype(int))

plt.bar(activity_names, activity_counts.values, color="steelblue")
plt.xlabel("Activity")
plt.ylabel("Number of Samples")
plt.title("Number of Samples per Activity (Balanced)")
plt.xticks(rotation=30)
plt.show()
