import React from 'react';
import { useApp } from '../../context/AppContext';
import { ShieldAlert, Activity, Cpu, MapPin } from 'lucide-react';

export const Header = () => {
  const { activeTab, setActiveTab, incidents, lastUpdated } = useApp();
  const activeCount = incidents.filter(i => i.status !== 'closed').length;

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between shadow-lg">
      <div className="flex items-center space-x-4">
        <div className="bg-blue-600/20 p-2 rounded-lg border border-blue-500/30">
          <ShieldAlert className="w-6 h-6 text-blue-400" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-wide text-slate-100 flex items-center gap-2">
            KSPDB LT Fault Localization Platform
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">
              Subdivision 07
            </span>
          </h1>
          <p className="text-xs text-slate-400">Control Room Console • 2 a.m. Operator Mode</p>
        </div>
      </div>

      <nav className="flex space-x-2 bg-slate-950 p-1 rounded-xl border border-slate-800">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'dashboard'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          Dashboard
          {activeCount > 0 && (
            <span className="bg-rose-500 text-white text-[10px] px-1.5 py-0.2 rounded-full font-bold">
              {activeCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('detail')}
          className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'detail'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <MapPin className="w-3.5 h-3.5" />
          Incident Details
        </button>

        <button
          onClick={() => setActiveTab('simulator')}
          className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'simulator'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          Fault Simulator
        </button>
      </nav>

      <div className="flex items-center space-x-3 text-xs text-slate-400">
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>Live 30s Polling</span>
        </div>
        <span className="text-slate-700">|</span>
        <span>Updated {lastUpdated.toLocaleTimeString()}</span>
      </div>
    </header>
  );
};
