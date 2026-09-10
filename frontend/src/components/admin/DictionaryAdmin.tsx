import React, { useEffect, useState } from "react";
import { Loader2, RefreshCw, Trash2, Plus, Volume2, Edit2, Save, X } from "lucide-react";
import * as authService from "../../services/authService";

export default function DictionaryAdmin() {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);

  // Form states
  const [domain, setDomain] = useState("CNTT");
  const [word, setWord] = useState("");
  const [translation, setTranslation] = useState("");
  const [pos, setPos] = useState("");
  const [phonetic, setPhonetic] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Bulk edit & Inline edit states
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<any>({});

  const fetchDictionary = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8003/api/v1/admin/dictionary`, {
      });
      if (res.ok) {
        const data = await res.json();
        setEntries(data.data || []);
      }
    } catch (error) {
      console.error("Failed to fetch dictionary", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDictionary();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!word.trim() || !translation.trim() || !domain.trim()) return;

    setAdding(true);
    setErrorMsg("");
    try {
      const res = await fetch(`http://localhost:8003/api/v1/admin/dictionary`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ 
          domain, 
          word: word.trim(), 
          translation: translation.trim(),
          pos: pos.trim(),
          phonetic: phonetic.trim()
        })
      });
      
      const data = await res.json();
      if (res.ok && data.ok) {
        setWord("");
        setTranslation("");
        setPos("");
        setPhonetic("");
        fetchDictionary();
      } else {
        setErrorMsg(data.detail || "Có lỗi xảy ra khi thêm từ.");
      }
    } catch (err: any) {
      setErrorMsg("Lỗi mạng khi gọi API.");
    } finally {
      setAdding(false);
    }
  };

  const handlePlayAudio = (url: string) => {
    if (!url) return;
    const audio = new Audio(url);
    audio.play().catch(e => console.error("Error playing audio:", e));
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa từ này?")) return;
    try {
      const res = await fetch(`http://localhost:8003/api/v1/admin/dictionary/${id}`, {
        method: "DELETE",
      });
      if (res.ok) fetchDictionary();
      else alert("Lỗi khi xóa từ!");
    } catch (e) {
      console.error(e);
      alert("Lỗi mạng khi xóa từ!");
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await fetch(`http://localhost:8003/api/v1/admin/dictionary/import`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        alert(`Nhập dữ liệu thành công! Đã thêm ${data.data.imported_count} từ vựng.`);
        fetchDictionary();
      } else {
        alert(data.detail || "Lỗi khi nhập dữ liệu.");
      }
    } catch (err) {
      alert("Lỗi kết nối khi tải file lên.");
    } finally {
      setLoading(false);
      e.target.value = ''; // reset input
    }
  };

  const handleToggleSelectAll = () => {
    if (selectedIds.length === entries.length && entries.length > 0) {
      setSelectedIds([]);
    } else {
      setSelectedIds(entries.map(e => e.id));
    }
  };

  const handleToggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(i => i !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleBulkDelete = async () => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa ${selectedIds.length} từ đã chọn?`)) return;
    try {
      const res = await fetch(`http://localhost:8003/api/v1/admin/dictionary/bulk-delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: selectedIds })
      });
      if (res.ok) {
        setSelectedIds([]);
        fetchDictionary();
      } else {
        alert("Lỗi khi xóa nhiều từ!");
      }
    } catch (e) {
      console.error(e);
      alert("Lỗi mạng khi xóa!");
    }
  };

  const startEdit = (entry: any) => {
    setEditingId(entry.id);
    setEditForm({
      domain: entry.domain,
      word: entry.word,
      translation: entry.translation,
      pos: entry.pos || "",
      phonetic: entry.phonetic || ""
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };

  const handleSaveEdit = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8003/api/v1/admin/dictionary/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm)
      });
      if (res.ok) {
        setEditingId(null);
        fetchDictionary();
      } else {
        alert("Lỗi khi cập nhật từ!");
      }
    } catch (e) {
      console.error(e);
      alert("Lỗi mạng khi cập nhật!");
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <p className="text-slate-600 dark:text-slate-400">
          Quản lý danh sách từ điển chuyên ngành cho hệ thống dịch thuật Real-time.
        </p>
        <div className="flex items-center gap-2 shrink-0">
          {selectedIds.length > 0 && (
            <button onClick={handleBulkDelete} className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-medium transition-colors text-sm flex items-center gap-2 h-[38px]">
              <Trash2 size={16} /> Xóa {selectedIds.length} mục
            </button>
          )}
          <label className="cursor-pointer bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 px-4 py-2 rounded-lg font-medium transition-colors text-sm flex items-center gap-2 h-[38px]">
            Import CSV/JSON
            <input type="file" accept=".csv,.json" className="hidden" onChange={handleImport} />
          </label>
          <button onClick={fetchDictionary} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500 transition-colors h-[38px]">
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin text-blue-500' : ''}`} />
          </button>
        </div>
      </div>

      <form onSubmit={handleAdd} className="bg-slate-50 dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-wrap gap-4 items-end">
        <div className="flex-1 min-w-[150px]">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Lĩnh vực</label>
          <input 
            type="text" 
            required
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
            placeholder="VD: CNTT"
          />
        </div>
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Từ gốc (EN)</label>
          <input 
            type="text" 
            required
            value={word}
            onChange={(e) => setWord(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
            placeholder="VD: array"
          />
        </div>
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nghĩa tiếng Việt</label>
          <input 
            type="text" 
            required
            value={translation}
            onChange={(e) => setTranslation(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
            placeholder="VD: mảng"
          />
        </div>
        <div className="flex-1 min-w-[120px]">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Loại từ</label>
          <input 
            type="text" 
            value={pos}
            onChange={(e) => setPos(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
            placeholder="VD: noun"
          />
        </div>
        <div className="flex-1 min-w-[120px]">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Phiên âm</label>
          <input 
            type="text" 
            value={phonetic}
            onChange={(e) => setPhonetic(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
            placeholder="VD: /əˈreɪ/"
          />
        </div>
        <button 
          type="submit" 
          disabled={adding}
          className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2 h-[42px]"
        >
          {adding ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />}
          Thêm
        </button>
      </form>
      
      {errorMsg && <p className="text-red-500 text-sm mt-2">{errorMsg}</p>}

      <div className="overflow-x-auto border border-slate-200 dark:border-slate-700 rounded-lg">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400 font-medium border-b border-slate-200 dark:border-slate-700">
            <tr>
              <th className="px-4 py-4 w-10 text-center">
                <input 
                  type="checkbox" 
                  checked={entries.length > 0 && selectedIds.length === entries.length}
                  onChange={handleToggleSelectAll}
                  className="rounded border-slate-300 cursor-pointer w-4 h-4"
                />
              </th>
              <th className="px-4 py-4">Lĩnh vực</th>
              <th className="px-4 py-4">Từ gốc</th>
              <th className="px-4 py-4">Loại từ</th>
              <th className="px-4 py-4">Phiên âm</th>
              <th className="px-4 py-4">Bản dịch</th>
              <th className="px-4 py-4">Ngày thêm</th>
              <th className="px-4 py-4 w-32 text-center">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {loading ? (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-slate-500">
                  <div className="flex justify-center items-center gap-2">
                    <Loader2 className="w-5 h-5 animate-spin" /> Đang tải từ vựng...
                  </div>
                </td>
              </tr>
            ) : entries.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-slate-500">
                  Chưa có từ vựng chuyên ngành nào.
                </td>
              </tr>
            ) : (
              entries.map((entry) => (
                <tr key={entry.id} className={`hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors ${selectedIds.includes(entry.id) ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''}`}>
                  <td className="px-4 py-4 text-center">
                    <input 
                      type="checkbox" 
                      checked={selectedIds.includes(entry.id)} 
                      onChange={() => handleToggleSelect(entry.id)} 
                      className="rounded border-slate-300 cursor-pointer w-4 h-4" 
                    />
                  </td>
                  {editingId === entry.id ? (
                    <>
                      <td className="px-4 py-4">
                        <input className="w-full border border-slate-300 dark:border-slate-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" value={editForm.domain} onChange={e => setEditForm({...editForm, domain: e.target.value})} />
                      </td>
                      <td className="px-4 py-4">
                        <input className="w-full border border-slate-300 dark:border-slate-600 rounded px-2 py-1.5 text-sm font-mono bg-white dark:bg-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" value={editForm.word} onChange={e => setEditForm({...editForm, word: e.target.value})} />
                      </td>
                      <td className="px-4 py-4">
                        <input className="w-full border border-slate-300 dark:border-slate-600 rounded px-2 py-1.5 text-sm italic bg-white dark:bg-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" value={editForm.pos} onChange={e => setEditForm({...editForm, pos: e.target.value})} />
                      </td>
                      <td className="px-4 py-4">
                        <input className="w-full border border-slate-300 dark:border-slate-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" value={editForm.phonetic} onChange={e => setEditForm({...editForm, phonetic: e.target.value})} />
                      </td>
                      <td className="px-4 py-4">
                        <input className="w-full border border-slate-300 dark:border-slate-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" value={editForm.translation} onChange={e => setEditForm({...editForm, translation: e.target.value})} />
                      </td>
                      <td className="px-4 py-4 text-slate-500 whitespace-nowrap text-xs">
                        {new Date(entry.created_at).toLocaleString('vi-VN')}
                      </td>
                      <td className="px-4 py-4 text-center flex justify-center gap-1">
                        <button onClick={() => handleSaveEdit(entry.id)} className="text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-900/20 p-2 rounded-full transition-colors" title="Lưu">
                          <Save size={18} />
                        </button>
                        <button onClick={cancelEdit} className="text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 p-2 rounded-full transition-colors" title="Hủy">
                          <X size={18} />
                        </button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-4 font-medium text-blue-600 dark:text-blue-400">
                        {entry.domain}
                      </td>
                      <td className="px-4 py-4 font-mono font-medium text-slate-900 dark:text-slate-100">
                        {entry.word}
                      </td>
                      <td className="px-4 py-4 text-slate-600 dark:text-slate-400 italic">
                        {entry.pos || "-"}
                      </td>
                      <td className="px-4 py-4 text-slate-600 dark:text-slate-400">
                        {entry.phonetic || "-"}
                      </td>
                      <td className="px-4 py-4 text-slate-700 dark:text-slate-300">
                        {entry.translation}
                      </td>
                      <td className="px-4 py-4 text-slate-500 whitespace-nowrap text-xs">
                        {new Date(entry.created_at).toLocaleString('vi-VN')}
                      </td>
                      <td className="px-4 py-4 text-center flex justify-center gap-1">
                        <button 
                          onClick={() => handlePlayAudio(entry.audio_url)}
                          disabled={!entry.audio_url}
                          className={`p-2 rounded-full transition-colors ${entry.audio_url ? 'text-blue-500 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20' : 'text-slate-300 dark:text-slate-600 cursor-not-allowed'}`}
                          title={entry.audio_url ? "Nghe phát âm" : "Đang tạo âm thanh ngầm..."}
                        >
                          <Volume2 size={18} />
                        </button>
                        <button 
                          onClick={() => startEdit(entry)}
                          className="text-amber-500 hover:text-amber-700 hover:bg-amber-50 dark:hover:bg-amber-900/20 p-2 rounded-full transition-colors"
                          title="Sửa từ vựng"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button 
                          onClick={() => handleDelete(entry.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 p-2 rounded-full transition-colors"
                          title="Xóa từ vựng"
                        >
                          <Trash2 size={18} />
                        </button>
                      </td>
                    </>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
