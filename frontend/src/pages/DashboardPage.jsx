import React from 'react';
import { NetworkMap } from '../components/map/NetworkMap';
import { IncidentList } from '../components/incidents/IncidentList';
import { DeviceHealthWidget } from '../components/status/DeviceHealthWidget';
import { SystemHealthWidget } from '../components/status/SystemHealthWidget';
import { StatisticsWidget } from '../components/status/StatisticsWidget';
import { useApp } from '../context/AppContext';

export const DashboardPage = () => {
  const { incidents } = useApp();

  return (
    <div className="flex h-full w-full overflow-hidden bg-slate-950">
      {/* Incident List Drawer (Left) */}
      <div className="w-96 flex-shrink-0 h-full">
        <IncidentList />
      </div>

      {/* Map + Health Dashboard Center & Right */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Leaflet Network Map */}
        <div className="flex-1 relative border-b border-slate-800">
          <NetworkMap />
        </div>

        {/* Health Widgets Footer Bar */}
        <div className="h-44 bg-slate-900 border-t border-slate-800 p-4 grid grid-cols-3 gap-4">
          <StatisticsWidget incidents={incidents} />
          <DeviceHealthWidget />
          <SystemHealthWidget />
        </div>
      </div>
    </div>
  );
};
