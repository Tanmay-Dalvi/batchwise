import React from 'react';
import { Layers, Sparkles, BookOpen, History, LayoutDashboard, Circle } from 'lucide-react';
import { Badge } from '../common/Badge';

export type ActiveTab = 'dashboard' | 'costing' | 'ai' | 'recipes' | 'history';

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  isBackendHealthy: boolean | null;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  isBackendHealthy,
}) => {
  const tabs = [
    { id: 'dashboard' as ActiveTab, label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'costing' as ActiveTab, label: 'Cost a Batch', icon: <Layers className="w-4 h-4" /> },
    { id: 'ai' as ActiveTab, label: 'AI Note Entry', icon: <Sparkles className="w-4 h-4" /> },
    { id: 'recipes' as ActiveTab, label: 'Saved Recipes', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'history' as ActiveTab, label: 'Batch History', icon: <History className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-stone-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Product Identity */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => onTabChange('dashboard')}
              className="flex items-center gap-2.5 text-left group focus:outline-none"
            >
              <div className="w-9 h-9 rounded-lg bg-forest-900 text-white flex items-center justify-center font-bold text-lg shadow-xs group-hover:bg-forest-950 transition-colors">
                <span className="font-mono text-lime-400 font-extrabold text-base">B</span>
                <span className="text-white text-xs -ml-0.5">₹</span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold tracking-tight text-charcoal-900 leading-none">
                    Batch<span className="text-forest-700">wise</span>
                  </span>
                  <Badge variant="lime" size="sm">Local-First</Badge>
                </div>
                <p className="text-[11px] text-stone-500 font-medium tracking-tight mt-0.5 hidden sm:block">
                  Every batch. Every cost. Every rupee.
                </p>
              </div>
            </button>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1 bg-cream-100 p-1 rounded-xl border border-stone-200">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all select-none ${
                    isActive
                      ? 'bg-forest-900 text-white shadow-xs'
                      : 'text-stone-600 hover:text-charcoal-900 hover:bg-white/60'
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              );
            })}
          </nav>

          {/* Health Status Indicator */}
          <div className="flex items-center gap-2">
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                isBackendHealthy === true
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : isBackendHealthy === false
                  ? 'bg-rose-50 text-rose-800 border-rose-200'
                  : 'bg-stone-50 text-stone-600 border-stone-200'
              }`}
              title={
                isBackendHealthy === true
                  ? 'Local calculation server & SQLite connected'
                  : 'Backend server connection unavailable'
              }
            >
              <Circle
                className={`w-2 h-2 fill-current ${
                  isBackendHealthy === true
                    ? 'text-emerald-500 animate-pulse'
                    : isBackendHealthy === false
                    ? 'text-rose-500'
                    : 'text-stone-400'
                }`}
              />
              <span className="text-[11px] font-mono hidden sm:inline">
                {isBackendHealthy === true ? 'Server: Active' : isBackendHealthy === false ? 'Server: Offline' : 'Checking...'}
              </span>
            </div>
          </div>
        </div>

        {/* Mobile Horizontal Tab Navigation */}
        <div className="md:hidden flex overflow-x-auto py-2 gap-1 scrollbar-none border-t border-stone-100">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap shrink-0 transition-colors ${
                  isActive
                    ? 'bg-forest-900 text-white font-semibold'
                    : 'bg-cream-200 text-charcoal-800 hover:bg-stone-200'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};

