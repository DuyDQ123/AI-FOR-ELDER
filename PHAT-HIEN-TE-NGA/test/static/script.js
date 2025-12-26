const accelCtx = document.getElementById("accelChart").getContext("2d");
const gyroCtx = document.getElementById("gyroChart").getContext("2d");
const MAX_DATA_POINTS = 50; // Giới hạn số điểm hiển thị

// Biểu đồ Gia tốc kế
const accelChart = new Chart(accelCtx, {
    type: "line",
    data: {
        labels: [],
        datasets: [
            { label: "AccelX", borderColor: "red", backgroundColor: "rgba(255, 0, 0, 0.2)", borderWidth: 2, data: [], fill: true },
            { label: "AccelY", borderColor: "green", backgroundColor: "rgba(0, 255, 0, 0.2)", borderWidth: 2, data: [], fill: true },
            { label: "AccelZ", borderColor: "blue", backgroundColor: "rgba(0, 0, 255, 0.2)", borderWidth: 2, data: [], fill: true },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        elements: { line: { tension: 0.3 } },
        scales: {
            x: { title: { display: true, text: "Thời gian (giây)" }, ticks: { autoSkip: true, maxTicksLimit: 10 } },
            y: { title: { display: true, text: "Gia tốc (m/s²)" }, beginAtZero: false },
        },
    },
});

// Biểu đồ Con quay hồi chuyển
const gyroChart = new Chart(gyroCtx, {
    type: "line",
    data: {
        labels: [],
        datasets: [
            { label: "GyroX", borderColor: "purple", backgroundColor: "rgba(128, 0, 128, 0.2)", borderWidth: 2, data: [], fill: true },
            { label: "GyroY", borderColor: "orange", backgroundColor: "rgba(255, 165, 0, 0.2)", borderWidth: 2, data: [], fill: true },
            { label: "GyroZ", borderColor: "pink", backgroundColor: "rgba(255, 192, 203, 0.2)", borderWidth: 2, data: [], fill: true },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        elements: { line: { tension: 0.3 } },
        scales: {
            x: { title: { display: true, text: "Thời gian (giây)" }, ticks: { autoSkip: true, maxTicksLimit: 10 } },
            y: { title: { display: true, text: "Vận tốc góc (°/s)" }, beginAtZero: false },
        },
    },
});

function updateAction() {
    fetch("/latest_action")
        .then(response => response.json())
        .then(data => {
            const actionElement = document.getElementById("action");
            actionElement.innerText = data.action;

            let bgColor = "white";

            switch (data.action) {
                case "Ngã về phía trước":
                    actionElement.style.color = "#d32f2f";
                    bgColor = "#ffebee";
                    break;
                case "Ngã về phía sau":
                    actionElement.style.color = "#1976d2";
                    bgColor = "#e3f2fd";
                    break;
                case "Ngã sang trái":
                    actionElement.style.color = "#388e3c";
                    bgColor = "#e8f5e9";
                    break;
                case "Ngã sang phải":
                    actionElement.style.color = "#f57c00";
                    bgColor = "#fff3e0";
                    break;
                default:
                    actionElement.style.color = "#333";
            }

            document.querySelector(".container").style.backgroundColor = bgColor;
        })
        .catch(error => console.error("Lỗi khi lấy dữ liệu:", error));
}

function updateSensorData() {
    fetch("/sensor_data")
        .then(response => response.json())
        .then(data => {
            console.log("Dữ liệu nhận được:", data); // Kiểm tra dữ liệu cảm biến

            if (data.time.length === 0) return; // Nếu không có dữ liệu, không làm gì cả

            const lastTime = new Date(data.time[data.time.length - 1] * 1000).toLocaleTimeString();

            if (accelChart.data.labels.length >= MAX_DATA_POINTS) {
                accelChart.data.labels.shift();
                accelChart.data.datasets.forEach(dataset => dataset.data.shift());
                gyroChart.data.labels.shift();
                gyroChart.data.datasets.forEach(dataset => dataset.data.shift());
            }

            accelChart.data.labels.push(lastTime);
            accelChart.data.datasets[0].data.push(parseFloat(data.ax[data.ax.length - 1].toFixed(2)));
            accelChart.data.datasets[1].data.push(parseFloat(data.ay[data.ay.length - 1].toFixed(2)));
            accelChart.data.datasets[2].data.push(parseFloat(data.az[data.az.length - 1].toFixed(2)));
            accelChart.update();

            gyroChart.data.labels.push(lastTime);
            gyroChart.data.datasets[0].data.push(parseFloat(data.gx[data.gx.length - 1].toFixed(2)));
            gyroChart.data.datasets[1].data.push(parseFloat(data.gy[data.gy.length - 1].toFixed(2)));
            gyroChart.data.datasets[2].data.push(parseFloat(data.gz[data.gz.length - 1].toFixed(2)));
            gyroChart.update();
        })
        .catch(error => console.error("Lỗi khi lấy dữ liệu cảm biến:", error));
}

setInterval(updateAction, 1000);
setInterval(updateSensorData, 1000);