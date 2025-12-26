import pandas as pd
import matplotlib.pyplot as plt

# Đọc dữ liệu từ file CSV 
file_path = "F:/orb/Bai tap on luyen/PHAT-HIEN-TE-NGA_1-main/PHAT-HIEN-TE-NGA/truc_quan_hoa_du_lieu/data_action.csv"
df = pd.read_csv(file_path)

# Kiểm tra xem có cột nào chứa thông tin hoạt động không
activity_column = None
for col in df.columns:
    if df[col].isin(["fall_forward", "fall_backward", "fall_left", "fall_right", "standing"]).any():
        activity_column = col
        break

if activity_column is None:
    raise KeyError("Không tìm thấy cột chứa thông tin hoạt động! Hãy kiểm tra lại dữ liệu.")

# Danh sách các hoạt động cần vẽ
activities = ["fall_forward", "fall_backward", "fall_left", "fall_right", "standing"]

# Lặp qua từng hoạt động để vẽ biểu đồ
for activity in activities:
    df_activity = df[df[activity_column] == activity]  # Lọc dữ liệu theo hoạt động

    plt.figure(figsize=(12, 5))

    # Vẽ dữ liệu từ gia tốc kế
    plt.subplot(2, 1, 1)
    plt.plot(df_activity.index, df_activity["AccelX"], label="AccelX")
    plt.plot(df_activity.index, df_activity["AccelY"], label="AccelY")
    plt.plot(df_activity.index, df_activity["AccelZ"], label="AccelZ")
    plt.title(f"Gia tốc kế - {activity}")
    plt.ylabel("m/s²")
    plt.legend()
    plt.grid()

    # Vẽ dữ liệu từ con quay hồi chuyển
    plt.subplot(2, 1, 2)
    plt.plot(df_activity.index, df_activity["GyroX"], label="GyroX")
    plt.plot(df_activity.index, df_activity["GyroY"], label="GyroY")
    plt.plot(df_activity.index, df_activity["GyroZ"], label="GyroZ")
    plt.title(f"Con quay hồi chuyển - {activity}")
    plt.ylabel("Độ/s")
    plt.legend()
    plt.grid()

    # Hiển thị biểu đồ
    plt.tight_layout()
    plt.show()
