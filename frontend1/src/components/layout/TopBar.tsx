import { Bell, Grid3x3, Plus } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";

interface TopBarProps {
  title?: string;
}

export function TopBar({ title = "IUH Portal AI" }: TopBarProps) {
  const { user } = useAuth();

  return (
    <header className="flex h-14 flex-shrink-0 items-center justify-between border-b border-slate-200 bg-white px-5">
      <h1 className="text-base font-semibold text-[#152a6e]">{title}</h1>

      <div className="flex items-center gap-3">
        <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" title="Notifications">
          <Bell size={18} />
        </button>
        <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" title="Apps">
          <Grid3x3 size={18} />
        </button>
        <button className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-700">
          <Plus size={16} />
          New Task
        </button>
        <div className="h-8 w-8 overflow-hidden rounded-full bg-slate-200">
          {user?.avatarUrl ? (
            <img src={user.avatarUrl} alt={user.fullName} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-xs font-semibold text-slate-500">
              {user?.fullName?.charAt(0) ?? "U"}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
