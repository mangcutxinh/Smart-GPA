import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("smartgpa.ml_service")

async def predict_failure_risk(diem_thuong_ky: float, diem_giua_ky: float) -> float:
    """
    Guửi điểm thành phần sang Databricks MLflow Model Serving Endpoint của bạn B (ML Engineer)
    để dự đoán xác suất rớt môn (từ 0.0 đến 1.0).
    """
    host = settings.DATABRICKS_ML_SERVER_HOSTNAME
    token = settings.DATABRICKS_ML_TOKEN
    endpoint = settings.DATABRICKS_ML_ENDPOINT_NAME
    http_path = settings.DATABRICKS_ML_HTTP_PATH

    # 1. Nếu có cấu hình ML Workspace thật -> Gọi API Databricks
    if host and token:
        # Xây dựng url đầy đủ từ http_path hoặc host
        if http_path:
            # Nếu http_path có dạng /serving-endpoints/endpoint_name/invocations
            url = f"https://{host}{http_path}"
        else:
            url = f"https://{host}/serving-endpoints/{endpoint}/invocations"
            
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Gửi dữ liệu dưới cả hai cách đặt tên cột (tránh lệch khớp tên biến của bạn ML)
        payload = {
            "dataframe_records": [
                {
                    "diem_thuong_ky_trung_binh": diem_thuong_ky,
                    "diem_thong_thuong": diem_thuong_ky,
                    "diem_giua_ky": diem_giua_ky
                }
            ]
        }

        try:
            logger.info(f"Connecting to MLflow Serving Endpoint: {url}...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    predictions = data.get("predictions", [0.0])
                    # Nếu trả về list/dict, ta trích xuất giá trị xác suất rớt
                    probability = predictions[0] if isinstance(predictions, list) else float(predictions)
                    logger.info(f"[SUCCESS] MLflow Predict: {probability:.2%}")
                    return probability
                else:
                    logger.error(f"[ERROR] MLflow Serving returned: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to query MLflow Serving Endpoint: {e}")

    # 2. Local Fallback (Giả lập thông minh nếu chạy offline/local)
    logger.info("Using local fallback prediction model.")
    dtb = (diem_thuong_ky + diem_giua_ky) / 2
    if dtb < 4.0:
        return 0.82  # Điểm < 4.0 -> Nguy cơ rớt môn cực cao (82%)
    elif dtb < 5.5:
        return 0.35  # Điểm trung bình yếu -> Nguy cơ vừa phải (35%)
    else:
        return 0.05  # Điểm an toàn -> Nguy cơ cực thấp (5%)
