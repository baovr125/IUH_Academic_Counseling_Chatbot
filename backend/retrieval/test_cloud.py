import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# 1. Dán chuỗi kết nối hoàn chỉnh của bạn vào đây
MONGO_URI = "mongodb+srv://iuh_admin:hdMMw6WKShqoWsK0@iuh-chatbot-cluster.nyg6xvj.mongodb.net/?appName=iuh-chatbot-cluster"

async def test_connection():
    try:
        print("⏳ Đang kết nối tới MongoDB Atlas trên Cloud...")
        # Khởi tạo client kết nối
        client = AsyncIOMotorClient(MONGO_URI)
        
        # Chọn hoặc tạo Database tên là 'iuh_chatbot_db'
        db = client["iuh_chatbot_db"]
        
        # Thử gửi lệnh ping lên server Cloud
        await client.admin.command('ping')
        print("✅ KẾT NỐI THÀNH CÔNG! Máy tính của bạn đã thông suốt với MongoDB Atlas.")
        
        # Thử tạo một bản ghi nháp vào collection 'users' để test
        test_user = {
            "username": "sv_test",
            "email": "test@student.iuh.edu.vn",
            "status": "Kết nối thành công thực tế từ máy local"
        }
        result = await db["users"].insert_one(test_user)
        print(f"📝 Đã ghi thử 1 bản ghi thành công. ID bản ghi: {result.inserted_id}")
        
    except Exception as e:
        print(f"❌ Kết nối thất bại. Lỗi: {e}")

# Chạy thử hàm kiểm tra
if __name__ == "__main__":
    asyncio.run(test_connection())