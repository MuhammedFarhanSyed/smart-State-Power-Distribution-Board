import React from 'react';
import { IncidentList } from '../components/incidents/IncidentList';
import { IncidentDetailPanel } from '../components/incidents/IncidentDetailPanel';

export const IncidentDetailPage = () => {
  return (
    <div className="flex h-full w-full overflow-hidden bg-slate-950">
      <div className="w-96 flex-shrink-0 h-full border-r border-slate-800">
        <IncidentList />
      </div>
      <div className="flex-1 h-full overflow-hidden">
        <IncidentDetailPanel />
      </div>
    </div>
  );
};
