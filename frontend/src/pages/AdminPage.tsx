import React, { useEffect, useState, useRef } from "react";
import { Database, UploadCloud, Globe, Play, X, Loader2, CheckCircle, AlertCircle, RefreshCw, Trash2, Edit2 } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

import * as authService from "../services/authService";

export default function AdminPage() {
  const { user } = useAuth();
    const [activeTab, setActiveTab] = useState<"files" | "urls" | "stats">("stats");

  const [documents, setDocuments] = useState<any[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");
  const [sortBy, setSortBy] = useState<"updated_at" | "chunk_count">("updated_at");
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchTerm), 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);
  const [totalItems, setTotalItems] = useState(0);

  const [editingDocId, setEditingDocId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [showExtractModal, setShowExtractModal] = useState(false);
  const [extraUrlsText, setExtraUrlsText] = useState("");



  useEffect(() => {
    if (activeTab === "stats") {
      fetchDocuments(currentPage, sortOrder, sortBy, debouncedSearch);
    }
  }, [activeTab, currentPage, sortOrder, sortBy, debouncedSearch]);

  const fetchDocuments = async (page: number = 1, sort: "desc" | "asc" = sortOrder, by: "updated_at" | "chunk_count" = sortBy, search: string = debouncedSearch) => {
    setLoadingDocs(true);
    try {
      const token = authService.getToken();
      const res = await fetch(`http://localhost:8000/api/admin/ingest/documents?page=${page}&limit=50&sort=${sort}&sort_by=${by}${search ? `&search=${encodeURIComponent(search)}` : ""}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.data || []);
        if (data.pagination) {
          setTotalPages(data.pagination.total_pages);
          setTotalItems(data.pagination.total_items);
        }
      }
    } catch (error) {
      console.error("Failed to fetch docs", error);
    } finally {
      setLoadingDocs(false);
    }
  };
  
  // File Upload State
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  
  // URL Crawler State
  const [urlsText, setUrlsText] = useState("");
  
  // Progress State
  const [status, setStatus] = useState<"idle" | "processing" | "completed" | "error">("idle");
  const [progressMsg, setProgressMsg] = useState("");
  const [progressPercent, setProgressPercent] = useState(0);
  
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Check if SSE needs to be connected
    if (status === "processing" && !eventSourceRef.current) {
      const token = authService.getToken() || "";
      // EventSource doesn't support custom headers easily, so we pass token in URL or rely on cookies.
      // But standard apiClient uses headers. Let's assume the backend doesn't strictly need the token in SSE or we can append it.
      // For now, since it's an admin endpoint, we pass it as a query param or just hit the endpoint if Kong Gateway passes auth.
      eventSourceRef.current = new EventSource(`http://localhost:8000/api/admin/ingest/status?token=${token}`);
      
      eventSourceRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setProgressMsg(data.message);
          setProgressPercent(data.progress || 0);
          
          if (data.status === "completed" || data.status === "error") {
            setStatus(data.status);
            if (eventSourceRef.current) {
              eventSourceRef.current.close();
              eventSourceRef.current = null;
            }
          }
        } catch (e) {
          console.error("Error parsing SSE data", e);
        }
      };
      
      eventSourceRef.current.onerror = () => {
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      };
    }
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [status]);

  if (!user || user.role !== "admin") {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center p-8 bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-red-200">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Access Denied</h2>
          <p className="text-slate-500 mt-2">Only administrators can access this portal.</p>
        </div>
      </div>
    );
  }

  const handleDeleteDocument = async (id: string) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa tài liệu này? Mọi chunk và dữ liệu vector liên quan sẽ bị xóa.")) return;
    try {
      const token = authService.getToken();
      const res = await fetch(`http://localhost:8000/api/admin/ingest/documents/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) fetchDocuments(currentPage);
      else alert("Lỗi khi xóa tài liệu!");
    } catch (e) {
      console.error(e);
      alert("Lỗi mạng khi xóa tài liệu!");
    }
  };

  const submitExtractAndCrawl = async () => {
    if (status === "processing") return;
    setStatus("processing");
    setProgressMsg("Đang khởi tạo tiến trình quét toàn bộ...");
    setProgressPercent(0);
    setShowExtractModal(false);

    try {
      const token = authService.getToken();
      const urls = extraUrlsText.split("\n").map((u) => u.trim()).filter((u) => u.startsWith("http"));
      const res = await fetch("http://localhost:8000/api/admin/ingest/extract-and-crawl", {
        method: "POST",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json" 
        },
        body: JSON.stringify({ extra_urls: urls }),
      });
      if (!res.ok) {
        setStatus("error");
        setProgressMsg("Lỗi khi gửi yêu cầu Quét toàn bộ.");
      }
    } catch (error) {
      console.error(error);
      setStatus("error");
      setProgressMsg("Không thể kết nối đến máy chủ.");
    }
  };

  const handleUpdateTitle = async (id: string) => {
    if (!editTitle.trim()) {
      setEditingDocId(null);
      return;
    }
    try {
      const token = authService.getToken();
      const res = await fetch(`http://localhost:8000/api/admin/ingest/documents/${id}`, {
        method: "PATCH",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ title: editTitle })
      });
      if (res.ok) {
        setDocuments(docs => docs.map(d => d.id === id ? { ...d, title: editTitle } : d));
      } else {
        alert("Lỗi khi cập nhật tên!");
      }
    } catch (e) {
      console.error(e);
      alert("Lỗi mạng khi cập nhật tên!");
    }
    setEditingDocId(null);
  };

  // --- Handlers ---
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)]);
    }
  };
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(prev => [...prev, ...Array.from(e.target.files as FileList)]);
    }
  };
  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const submitFiles = async () => {
    if (selectedFiles.length === 0) return;
    setStatus("processing");
    setProgressMsg("Đang chuẩn bị tải lên...");
    setProgressPercent(0);
    
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append("files", file);
    });

    try {
      const token = authService.getToken();
      const res = await fetch("http://localhost:8000/api/admin/ingest/files", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });
      if (!res.ok) throw new Error("Upload failed");
      setSelectedFiles([]);
    } catch (err: any) {
      setStatus("error");
      setProgressMsg(err.message || "Đã xảy ra lỗi khi tải lên.");
    }
  };

  const submitUrls = async () => {
    const urls = urlsText.split("\n").map(u => u.trim()).filter(u => u);
    if (urls.length === 0) return;
    setStatus("processing");
    setProgressMsg("Đang chuẩn bị cào dữ liệu...");
    setProgressPercent(0);

    try {
      const token = authService.getToken();
      const res = await fetch("http://localhost:8000/api/admin/ingest/urls", {
        method: "POST",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ urls })
      });
      if (!res.ok) throw new Error("Gửi URLs thất bại");
      setUrlsText("");
    } catch (err: any) {
      setStatus("error");
      setProgressMsg(err.message || "Đã xảy ra lỗi khi gửi URLs.");
    }
  };

  return (
    <div className="flex-1 overflow-auto bg-slate-50 p-8 dark:bg-slate-900">
      <div className="mx-auto max-w-7xl space-y-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <Database className="text-blue-600" /> Admin Data Ingestion
        </h1>

        {/* Status Dashboard */}
        {status !== "idle" && (
          <div className={`p-6 rounded-2xl shadow-sm border ${status === 'error' ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800' : 'bg-white border-slate-200 dark:bg-slate-800 dark:border-slate-700'}`}>
            <div className="flex items-center gap-4">
              {status === "processing" && <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />}
              {status === "completed" && <CheckCircle className="w-8 h-8 text-green-500" />}
              {status === "error" && <AlertCircle className="w-8 h-8 text-red-500" />}
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {status === "processing" ? "Hệ thống đang xử lý..." : status === "completed" ? "Hoàn tất!" : "Đã xảy ra lỗi"}
                </h3>
                <p className="text-slate-600 dark:text-slate-400">{progressMsg}</p>
                
                {status === "processing" && progressPercent > 0 && (
                  <div className="mt-3 h-2 w-full bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 rounded-full transition-all duration-500" 
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                )}
              </div>
              {(status === "completed" || status === "error") && (
                <button 
                  onClick={() => setStatus("idle")}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 rounded-lg font-medium"
                >
                  Đóng
                </button>
              )}
            </div>
          </div>
        )}

        {/* Main Interface */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setActiveTab("stats")}
              className={`flex-1 py-4 text-center font-medium flex items-center justify-center gap-2 ${
                activeTab === "stats" 
                  ? "border-b-2 border-blue-600 text-blue-600 bg-blue-50/50 dark:bg-blue-900/10" 
                  : "text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700/50"
              }`}
            >
              <Database size={18} /> Thống kê Tài liệu
            </button>
            <button
              onClick={() => setActiveTab("files")}
              className={`flex-1 py-4 text-center font-medium flex items-center justify-center gap-2 ${
                activeTab === "files" 
                  ? "border-b-2 border-blue-600 text-blue-600 bg-blue-50/50 dark:bg-blue-900/10" 
                  : "text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700/50"
              }`}
            >
              <UploadCloud size={18} /> Tải lên Tài liệu
            </button>
            <button
              onClick={() => setActiveTab("urls")}
              className={`flex-1 py-4 text-center font-medium flex items-center justify-center gap-2 ${
                activeTab === "urls" 
                  ? "border-b-2 border-blue-600 text-blue-600 bg-blue-50/50 dark:bg-blue-900/10" 
                  : "text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700/50"
              }`}
            >
              <Globe size={18} /> Cào dữ liệu Web
            </button>
          </div>

          <div className="p-6 md:p-8">
            {activeTab === "stats" && (
              <div className="space-y-6 animate-fade-in">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <p className="text-slate-600">Danh sách các tài liệu đã được nạp vào Vector Database.</p>
                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <div className="relative w-full sm:w-64">
                      <input 
                        type="text"
                        placeholder="Tìm kiếm theo Tên hoặc URL..."
                        value={searchTerm}
                        onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
                        className="w-full pl-3 pr-10 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                      />
                    </div>
                    <button onClick={() => fetchDocuments(currentPage, sortOrder, sortBy, debouncedSearch)} className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors shrink-0">
                      <RefreshCw className={`w-5 h-5 ${loadingDocs ? 'animate-spin text-blue-500' : ''}`} />
                    </button>
                  </div>
                </div>
                
                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-slate-600 font-medium border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-4 w-16 text-center">STT</th>
                        <th className="px-6 py-4">Tên tài liệu / Tiêu đề</th>
                        <th className="px-6 py-4">Nguồn (URL)</th>
                        <th className="px-6 py-4 cursor-pointer hover:bg-slate-200 transition-colors" onClick={() => { if(sortBy === "updated_at") { setSortOrder(sortOrder === "desc" ? "asc" : "desc"); } else { setSortBy("updated_at"); setSortOrder("desc"); } }}>
                          <div className="flex items-center gap-2">
                            Cập nhật lần cuối
                            <span className="text-xs">{sortBy === "updated_at" ? (sortOrder === "desc" ? "▼" : "▲") : ""}</span>
                          </div>
                        </th>
                        <th className="px-6 py-4 text-center cursor-pointer hover:bg-slate-200 transition-colors" onClick={() => { if(sortBy === "chunk_count") { setSortOrder(sortOrder === "desc" ? "asc" : "desc"); } else { setSortBy("chunk_count"); setSortOrder("desc"); } }}>
                          <div className="flex items-center justify-center gap-2">
                            Số Chunks
                            <span className="text-xs">{sortBy === "chunk_count" ? (sortOrder === "desc" ? "▼" : "▲") : ""}</span>
                          </div>
                        </th>
                        <th className="px-4 py-4 w-16 text-center">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {loadingDocs ? (
                        <tr>
                          <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                            <div className="flex justify-center items-center gap-2">
                              <Loader2 className="w-5 h-5 animate-spin" /> Đang tải dữ liệu...
                            </div>
                          </td>
                        </tr>
                      ) : documents.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                            Chưa có tài liệu nào trong cơ sở dữ liệu.
                          </td>
                        </tr>
                      ) : (
                        documents.map((doc: any, index: number) => (
                          <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                            <td className="px-4 py-4 text-center text-slate-500">
                              {(currentPage - 1) * 50 + index + 1}
                            </td>
                            <td className="px-6 py-4 font-medium text-slate-900 max-w-md" title={doc.title}>
                              {editingDocId === doc.id ? (
                                <input
                                  type="text"
                                  className="w-full border border-blue-500 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
                                  value={editTitle}
                                  onChange={(e) => setEditTitle(e.target.value)}
                                  onBlur={() => handleUpdateTitle(doc.id)}
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') handleUpdateTitle(doc.id);
                                    if (e.key === 'Escape') setEditingDocId(null);
                                  }}
                                  autoFocus
                                />
                              ) : (
                                <div 
                                  className="cursor-pointer hover:text-blue-600 line-clamp-2 flex items-center justify-between group"
                                  onClick={() => { setEditingDocId(doc.id); setEditTitle(doc.title || ""); }}
                                >
                                  <span>{doc.title || "Không có tiêu đề"}</span>
                                  <Edit2 size={14} className="ml-2 opacity-0 group-hover:opacity-100 text-slate-400 flex-shrink-0" />
                                </div>
                              )}
                            </td>
                            <td className="px-6 py-4">
                              <a href={doc.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline max-w-xs truncate inline-block" title={doc.source_url}>
                                {doc.source_url}
                              </a>
                            </td>
                            <td className="px-6 py-4 text-slate-500 whitespace-nowrap">
                              {new Date(doc.updated_at).toLocaleString('vi-VN')}
                            </td>
                            <td className="px-6 py-4 text-center font-medium text-slate-700">
                              {doc.chunk_count || 0}
                            </td>
                            <td className="px-4 py-4 text-center">
                              <button 
                                onClick={() => handleDeleteDocument(doc.id)}
                                className="text-red-500 hover:text-red-700 hover:bg-red-50 p-2 rounded-full transition-colors"
                                title="Xóa tài liệu"
                              >
                                <Trash2 size={18} />
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
                
                {totalPages > 1 && (
                  <div className="flex items-center justify-between mt-4">
                    <p className="text-sm text-slate-500">
                      Hiển thị tổng số {totalItems} tài liệu
                    </p>
                    <div className="flex space-x-2">
                      <button 
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1 || loadingDocs}
                        className="px-3 py-1 rounded border border-slate-200 text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
                      >
                        Trước
                      </button>
                      <span className="px-3 py-1 text-sm font-medium text-slate-700">
                        Trang {currentPage} / {totalPages}
                      </span>
                      <button 
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages || loadingDocs}
                        className="px-3 py-1 rounded border border-slate-200 text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
                      >
                        Sau
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "files" && (
              <div className="space-y-6 animate-fade-in">
                <div 
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${
                    isDragging 
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" 
                      : "border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                  }`}
                >
                  <UploadCloud className="mx-auto h-12 w-12 text-slate-400 mb-4" />
                  <p className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-1">
                    Kéo thả file vào đây, hoặc click để chọn
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                    Hỗ trợ PDF, TXT, MD
                  </p>
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.txt,.md"
                    className="hidden"
                    id="file-upload"
                    onChange={handleFileSelect}
                  />
                  <label 
                    htmlFor="file-upload"
                    className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
                  >
                    Chọn File
                  </label>
                </div>

                {selectedFiles.length > 0 && (
                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                      Đã chọn {selectedFiles.length} file:
                    </h4>
                    <ul className="space-y-2">
                      {selectedFiles.map((file, i) => (
                        <li key={i} className="flex items-center justify-between bg-white dark:bg-slate-800 p-2 rounded border border-slate-200 dark:border-slate-700">
                          <span className="text-sm text-slate-600 dark:text-slate-300 truncate">
                            {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                          </span>
                          <button onClick={() => removeFile(i)} className="text-slate-400 hover:text-red-500">
                            <X size={16} />
                          </button>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-4 flex justify-end">
                      <button
                        onClick={submitFiles}
                        disabled={status === "processing"}
                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                      >
                        <Play size={18} /> Bắt đầu Xử lý File
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {activeTab === "urls" && (
              <div className="space-y-6 animate-fade-in">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Danh sách URLs (Mỗi URL một dòng)
                  </label>
                  <textarea
                    value={urlsText}
                    onChange={(e) => setUrlsText(e.target.value)}
                    placeholder="https://iuh.edu.vn/tin-tuc-1&#10;https://iuh.edu.vn/tin-tuc-2"
                    className="w-full h-64 p-4 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none resize-none font-mono text-sm"
                  ></textarea>
                </div>
                <div className="flex justify-between items-center">
                  <button
                    onClick={() => setShowExtractModal(true)}
                    disabled={status === "processing"}
                    className="flex items-center gap-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 px-4 py-2.5 rounded-lg font-medium transition-colors"
                  >
                    <RefreshCw size={18} /> Quét Toàn Hệ Thống (Auto Crawl)
                  </button>
                  <button
                    onClick={submitUrls}
                    disabled={status === "processing" || !urlsText.trim()}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                  >
                    <Globe size={18} /> Bắt đầu Cào dữ liệu
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Extract Modal */}
      {showExtractModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden animate-fade-in">
            <div className="flex justify-between items-center p-6 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <RefreshCw className="text-indigo-500" /> Quét Toàn Hệ Thống
              </h3>
              <button onClick={() => setShowExtractModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={24} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="bg-blue-50 text-blue-800 p-4 rounded-lg border border-blue-100 text-sm">
                <p className="font-semibold mb-2">Chức năng này sẽ làm gì?</p>
                <ul className="list-disc pl-5 space-y-1">
                  <li>Tự động đọc Sitemap từ <strong>camnang.iuh.edu.vn</strong></li>
                  <li>Tự động quét các thông báo từ <strong>iuh.edu.vn/vi/thong-bao</strong></li>
                  <li>Tự động dùng thuật toán BFS vét cạn link từ trang chủ <strong>IUH</strong> và <strong>Cẩm Nang</strong></li>
                  <li>Quét đệ quy toàn bộ danh mục Quy chế, Điểm chuẩn, Đề án của <strong>Tuyển Sinh</strong></li>
                </ul>
                <p className="mt-2 text-red-600 font-medium">Lưu ý: Quá trình này sẽ cào hàng trăm trang web và mất rất nhiều thời gian!</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Thêm URL tùy chỉnh (Tuỳ chọn)
                </label>
                <textarea
                  value={extraUrlsText}
                  onChange={(e) => setExtraUrlsText(e.target.value)}
                  placeholder="https://tuyensinh.iuh.edu.vn/mot-trang-moi"
                  className="w-full h-32 p-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none resize-none font-mono text-sm"
                ></textarea>
                <p className="text-xs text-slate-500 mt-1">Các URL nhập ở đây sẽ được cào cùng với danh sách mặc định của hệ thống.</p>
              </div>
            </div>

            <div className="p-6 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 flex justify-end gap-3">
              <button
                onClick={() => setShowExtractModal(false)}
                className="px-5 py-2.5 rounded-lg font-medium text-slate-600 hover:bg-slate-200 transition-colors"
              >
                Hủy bỏ
              </button>
              <button
                onClick={submitExtractAndCrawl}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition-colors"
              >
                <Play size={18} /> Bắt đầu Quét Toàn Bộ
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
