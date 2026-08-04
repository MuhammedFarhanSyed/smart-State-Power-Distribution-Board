import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Header } from './components/layout/Header';
import { StatusBar } from './components/layout/StatusBar';
import { DashboardPage } from './pages/DashboardPage';
import { IncidentDetailPage } from './pages/IncidentDetailPage';
import { SimulatorPage } from './pages/SimulatorPage';

const MainContent = () => {
  const { activeTab, error } = useApp();

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 text-slate-100">
      <Header />

      {error && (
        <div className="bg-rose-950/90 border-b border-rose-800 text-rose-200 px-6 py-2 text-xs flex items-center justify-between">
          <span>⚠️ {error}</span>
          <span className="text-[10px] text-rose-400 font-mono">Control Room Connection Timeout</span>
        </div>
      )}

      <main className="flex-1 overflow-hidden relative">
        {activeTab === 'dashboard' && <DashboardPage />}
        {activeTab === 'detail' && <IncidentDetailPage />}
        {activeTab === 'simulator' && <SimulatorPage />}
      </main>

      <StatusBar />
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <MainContent />
    </AppProvider>
  );
}
