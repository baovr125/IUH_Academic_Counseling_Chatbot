# Ghi Chú Kỹ Thuật Khóa Luận: IUH Academic Counseling Chatbot (`academic_chatbot_service`)

> [!NOTE]
> File tài liệu này được khởi tạo sẵn làm placeholder. Nội dung chi tiết về RAG Pipeline (Hybrid RRF, Cross-Encoder Reranking, Semantic Cache, Guardrails, Chat History) sẽ do thành viên phụ trách Chatbot hoàn thiện.


 Xóa semantic cache (chỉ tài khoản admin; gửi JWT của admin qua Kong):

    curl -X DELETE -H "Authorization: Bearer <JWT_ADMIN>" http://localhost:8000/api/chat/messages/cache