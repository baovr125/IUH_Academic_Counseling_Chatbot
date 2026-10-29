import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { MobileNavDrawer } from "./MobileNavDrawer";

interface MainLayoutProps {
  title?: string;
}

/**
 * Khung ứng dụng "liền khối": thanh bên, thanh trên và nền trang dùng chung MỘT màu nền (không viền, không khối trắng riêng),
 * chỉ các thẻ nội dung nổi lên trên nền đó. Từ `md` trở lên có thanh icon bên trái; dưới `md` thay bằng ngăn kéo điều hướng.
 * `h-dvh` (dự phòng `h-screen`) để thanh địa chỉ của trình duyệt di động không che đáy trang.
 */
export function MainLayout({ title }: MainLayoutProps) {
  const [isNavOpen, setIsNavOpen] = useState(false);

  return (
    <div className="flex h-screen h-dvh w-full overflow-hidden bg-brand-50/70 dark:bg-slate-950 dark:text-slate-100">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={title} onOpenNav={() => setIsNavOpen(true)} />
        <main className="min-h-0 flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
      {isNavOpen && <MobileNavDrawer onClose={() => setIsNavOpen(false)} />}
    </div>
  );
}
