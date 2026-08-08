import React from 'react';
import { ViewMode } from '../../types';
import { useAuth } from '../../providers/AuthProvider';
import { getUserDisplayName, getUserInitials } from '../../utils/userUtils';
import { canViewViewMode, isStrictlyViewer } from '../../utils/permissions';
import { 
  LayoutDashboard, FolderKanban, FlaskConical, Dna, Bot, 
  Search, BarChart3, Bell, User, ShieldCheck, Eye,
  Layers, Activity, LogOut, ChevronRight, TestTube2, HardDrive, MapPin, LucideIcon
} from 'lucide-react';

interface SidebarProps {
  currentView: ViewMode;
  onSelectView: (view: ViewMode) => void;
  unreadCount: number;
}

interface MenuItem {
  id: ViewMode;
  label: string;
  icon: LucideIcon;
  badge?: string;
  count?: number;
  highlight?: boolean;
}

interface MenuGroup {
  group: string;
  items: MenuItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  currentView, 
  onSelectView,
  unreadCount 
}) => {
  const { logout, user } = useAuth();
  const displayName = getUserDisplayName(user);
  const initials = getUserInitials(user);
  const isViewer = isStrictlyViewer(user);

  const rawMenuGroups: MenuGroup[] = [
    {
      group: 'Core Research',
      items: [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'projects', label: 'Projects Workspace', icon: FolderKanban },
        { id: 'protocols', label: 'Protocol Management', icon: FolderKanban },
        { id: 'experiments', label: 'All Experiments', icon: FlaskConical },
        { id: 'eln', label: 'ELN Editor', icon: FlaskConical },
        { id: 'samples', label: 'Sample Registry', icon: TestTube2 },
        { id: 'inventory', label: 'Inventory Management', icon: TestTube2 },
        { id: 'instruments', label: 'Instrument Management', icon: TestTube2 },
        { id: 'sequence-registry', label: 'Sequence Management', icon: Dna },
        { id: 'sequences', label: 'Sequence Viewer', icon: Dna },
      ]
    },
    {
      group: 'Workspace & Management',
      items: [
        { id: 'admin', label: 'Admin Panel (RBAC)', icon: ShieldCheck },
        { id: 'settings', label: 'Settings', icon: User },
        { id: 'login', label: 'Sign Out', icon: LogOut },
      ]
    }
  ];

  const menuGroups = rawMenuGroups
    .map((group) => ({
      ...group,
      items: group.items.filter(item => item.id === 'login' || canViewViewMode(user, item.id))
    }))
    .filter((group) => group.items.length > 0);

  return (
    <aside className="w-64 bg-[#0F172A] text-slate-300 flex flex-col h-screen border-r border-slate-800 shrink-0 sticky top-0 print:hidden">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-teal-400 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
          <Dna className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-white tracking-wide text-lg">ELN</span>
          </div>
          <p className="text-xs text-slate-400 truncate max-w-[150px]">Unified R&D Platform</p>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {menuGroups.map((group, idx) => (
          <div key={idx}>
            <div className="px-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              {group.group}
            </div>
            <nav className="space-y-1">
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = currentView === item.id;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      if (item.id === 'login') {
                        logout();
                        onSelectView('login');
                      } else {
                        onSelectView(item.id);
                      }
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-all duration-150 group ${
                      isActive 
                        ? 'bg-blue-600 text-white font-medium shadow-md shadow-blue-600/25' 
                        : item.highlight
                        ? 'text-teal-400 hover:bg-slate-800/80 hover:text-teal-300 font-medium'
                        : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4 h-4 transition-transform group-hover:scale-110 ${
                        isActive ? 'text-white' : item.highlight ? 'text-teal-400' : 'text-slate-400 group-hover:text-slate-200'
                      }`} />
                      <span>{item.label}</span>
                    </div>

                    {item.badge && !isActive && (
                      <span className="text-[10px] font-semibold bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded border border-blue-500/20">
                        {item.badge}
                      </span>
                    )}

                    {item.count !== undefined && item.count > 0 && (
                      <span className="px-1.5 py-0.5 text-xs font-bold bg-rose-500 text-white rounded-full">
                        {item.count}
                      </span>
                    )}

                    {isActive && <ChevronRight className="w-3.5 h-3.5 text-white/70" />}
                  </button>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* User Profile Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/60">
        {isViewer && (
          <div className="flex items-center gap-1.5 px-2 py-1.5 mb-2 rounded-lg bg-purple-900/50 border border-purple-500/40">
            <Eye className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            <span className="text-[11px] font-bold text-purple-300 uppercase tracking-wide">Read-Only Access</span>
            <span className="ml-auto text-[9px] bg-purple-500/30 text-purple-300 px-1.5 py-0.5 rounded font-mono">VIEWER</span>
          </div>
        )}
        <div 
          onClick={() => onSelectView('settings')}
          className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <div className="relative">
            <div className={`w-9 h-9 rounded-full font-bold flex items-center justify-center text-sm ring-2 ${isViewer ? 'bg-gradient-to-r from-purple-600 to-indigo-600 ring-purple-400/30' : 'bg-gradient-to-r from-blue-500 to-indigo-600 ring-blue-400/30'} text-white`}>
              {initials}
            </div>
            <span className={`w-2.5 h-2.5 border-2 border-slate-900 rounded-full absolute bottom-0 right-0 ${isViewer ? 'bg-purple-400' : 'bg-emerald-500'}`}></span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-slate-100 truncate">{displayName}</p>
            {isViewer && (
              <p className="text-[10px] text-purple-400 font-medium">Inspection Mode</p>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};
