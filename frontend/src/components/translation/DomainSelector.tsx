import React, { useState, useRef, useEffect } from "react";
import { Search, ChevronDown, Check } from "lucide-react";

export interface DomainSelectorProps {
  value: string;
  onChange: (domain: string) => void;
}

const PREDEFINED_DOMAINS = [
  "Công nghệ Thông tin (IT)",
  "Y khoa / Sức khỏe",
  "Kinh tế / Tài chính",
  "Kỹ thuật Cơ khí",
  "Luật / Pháp lý",
  "Marketing",
];

export const DomainSelector: React.FC<DomainSelectorProps> = ({ value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredDomains = PREDEFINED_DOMAINS.filter(d => 
    d.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  // If search term is not in list, allow selecting it as a custom domain
  const showCustomOption = searchTerm.trim() !== "" && 
                           !PREDEFINED_DOMAINS.some(d => d.toLowerCase() === searchTerm.toLowerCase());

  return (
    <div className="relative" ref={dropdownRef}>
      <div 
        className="flex items-center justify-between w-64 px-4 py-2 bg-white border border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 focus-within:ring-2 focus-within:ring-blue-200 transition-all"
        onClick={() => setIsOpen(true)}
      >
        <span className="text-sm font-medium text-gray-700 truncate">
          {value || "Chọn lĩnh vực dịch thuật..."}
        </span>
        <ChevronDown size={16} className={`text-gray-400 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-xl top-full">
          <div className="p-2 border-b border-gray-100 flex items-center">
            <Search size={14} className="text-gray-400 ml-2 mr-2" />
            <input
              type="text"
              className="w-full text-sm outline-none bg-transparent"
              placeholder="Tìm hoặc nhập tên ngành..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoFocus
            />
          </div>
          
          <div className="max-h-60 overflow-y-auto p-1">
            <div 
              className={`px-3 py-2 text-sm rounded-md cursor-pointer flex items-center justify-between ${!value ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-700 hover:bg-gray-50"}`}
              onClick={() => {
                onChange("");
                setIsOpen(false);
              }}
            >
              <span>Dịch thông thường (Mặc định)</span>
              {!value && <Check size={14} />}
            </div>

            {filteredDomains.map(domain => (
              <div
                key={domain}
                className={`px-3 py-2 text-sm rounded-md cursor-pointer flex items-center justify-between ${value === domain ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-700 hover:bg-gray-50"}`}
                onClick={() => {
                  onChange(domain);
                  setIsOpen(false);
                  setSearchTerm("");
                }}
              >
                <span>{domain}</span>
                {value === domain && <Check size={14} />}
              </div>
            ))}
            
            {showCustomOption && (
              <div
                className={`px-3 py-2 text-sm rounded-md cursor-pointer flex items-center justify-between ${value === searchTerm ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-700 hover:bg-gray-50"}`}
                onClick={() => {
                  onChange(searchTerm);
                  setIsOpen(false);
                  setSearchTerm("");
                }}
              >
                <span>Thêm "{searchTerm}"</span>
              </div>
            )}
            
            {filteredDomains.length === 0 && !showCustomOption && (
              <div className="px-3 py-4 text-sm text-center text-gray-500">
                Không tìm thấy kết quả
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
