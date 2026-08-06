import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

interface MainLayoutProps {
  title?: string;
}

/**
 * Shell for every authenticated screen: fixed-width icon rail on the left,
 * a top bar, and a scrollable content region rendered via <Outlet /> so
 * each route owns its own page component.
 */
export function MainLayout({ title }: MainLayoutProps) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-50 dark:bg-slate-900 dark:text-slate-100">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={title} />
        <main className="min-h-0 flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
