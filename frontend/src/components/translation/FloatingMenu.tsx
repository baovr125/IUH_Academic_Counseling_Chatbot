import React from "react";
import { PlusCircle, Volume2, X } from "lucide-react";

export interface FloatingMenuProps {
  x: number;
  y: number;
  onSave: () => void;
  onSpeak: () => void;
  onClose: () => void;
  isSaving: boolean;
}

export const FloatingMenu: React.FC<FloatingMenuProps> = ({ x, y, onSave, onSpeak, onClose, isSaving }) => {
  return (
    <div 
      className="absolute z-50 flex items-center bg-gray-900 rounded-lg shadow-2xl animate-fade-in-up"
      style={{ left: `${x}px`, top: `${y}px`, transform: "translate(-50%, -100%)", marginTop: "-10px" }}
    >
      <div className="absolute w-3 h-3 bg-gray-900 rotate-45" style={{ bottom: "-6px", left: "50%", transform: "translateX(-50%) rotate(45deg)" }}></div>
      
      <button 
        className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800 rounded-l-lg transition-colors group"
        onClick={onSave}
        disabled={isSaving}
      >
        <PlusCircle size={16} className={`text-blue-400 group-hover:text-blue-300 ${isSaving ? 'animate-spin' : ''}`} />
        <span>{isSaving ? "Đang lưu..." : "Lưu thẻ"}</span>
      </button>
      
      <div className="w-px h-5 bg-gray-700"></div>
      
      <button 
        className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800 transition-colors group"
        onClick={onSpeak}
      >
        <Volume2 size={16} className="text-green-400 group-hover:text-green-300" />
        <span>Phát âm</span>
      </button>

      <div className="w-px h-5 bg-gray-700"></div>

      <button 
        className="flex items-center justify-center px-2 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-r-lg transition-colors"
        onClick={onClose}
      >
        <X size={16} />
      </button>
    </div>
  );
};
