import { useNavigate } from 'react-router-dom';
import { LayoutGrid, FolderClock, TrendingUp, Wallet, Plus, LogOut } from 'lucide-react';

const TABS = [
  { key: 'overview', number: '01', label: 'Overview', icon: LayoutGrid },
  { key: 'sessions', number: '02', label: 'Sessions', icon: FolderClock },
  { key: 'progress', number: '03', label: 'Progress', icon: TrendingUp },
  { key: 'billing', number: '04', label: 'Billing', icon: Wallet },
];

function DashboardLayout({ activeTab, onTabChange, user, onLogout, children }) {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-paper flex">
      {/* Sidebar - the docket. Dark to read as a ledger spine against the
          paper-toned content, not just a color swap of the same page. */}
      <aside className="w-64 flex-shrink-0 bg-ink flex flex-col">
        <div className="px-6 py-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-coral flex items-center justify-center font-display text-xs text-white flex-shrink-0">
              VM
            </div>
            <div className="min-w-0">
              <p className="font-display text-white text-base leading-tight truncate">VC Pitch Analyzer</p>
              <p className="text-[10px] font-mono uppercase tracking-widest text-white/40">Your Docket</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-6 space-y-1">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => onTabChange(tab.key)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  active
                    ? 'bg-white/10 text-white'
                    : 'text-white/55 hover:text-white/85 hover:bg-white/5'
                }`}
              >
                <span className={`font-mono text-[10px] w-4 flex-shrink-0 ${active ? 'text-coral' : 'text-white/30'}`}>
                  {tab.number}
                </span>
                <Icon className="w-4 h-4 flex-shrink-0" strokeWidth={1.75} />
                <span className="truncate">{tab.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="px-3 pb-4">
          <button
            onClick={() => navigate('/personas')}
            className="w-full flex items-center justify-center gap-2 bg-coral hover:bg-coral-bright text-white text-sm font-medium rounded-lg px-3 py-2.5 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Session
          </button>
        </div>

        <div className="px-6 py-5 border-t border-white/10">
          <p className="text-xs text-white/50 truncate mb-2">{user?.email}</p>
          <button
            onClick={onLogout}
            className="flex items-center gap-1.5 text-xs text-white/50 hover:text-white/85 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            Log Out
          </button>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-8 py-10">{children}</div>
      </main>
    </div>
  );
}

export default DashboardLayout;
