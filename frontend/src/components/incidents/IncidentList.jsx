import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { IncidentCard } from './IncidentCard';
import { Filter, Inbox } from 'lucide-react';

export const IncidentList = () => {
  const { incidents, selectIncident, handleAcknowledge, loading } = useApp();
  const [filter, setFilter] = useState('all'); // 'all' | 'active' | 'resolved' | 'closed'

  const filteredIncidents = incidents.filter(i => {
    if (filter === 'active') return i.status !== 'closed' && i.status !== 'verified';
    if (filter === 'resolved') return i.status === 'resolved' || i.status === 'verified';
    if (filter === 'closed') return i.status === 'closed';
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-slate-950 border-r border-slate-800">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-blue-400" />
          Active Incident Stream ({filteredIncidents.length})
        </h2>

        <div className="flex space-x-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-[10px]">
          {['all', 'active', 'closed'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2 py-1 rounded capitalize font-semibold ${
                filter === f ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading && incidents.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-xs">
            Loading grid incidents...
          </div>
        ) : filteredIncidents.length === 0 ? (
          <div className="text-center py-16 text-slate-500 flex flex-col items-center">
            <Inbox className="w-8 h-8 text-slate-700 mb-2" />
            <p className="text-xs font-medium">No incidents match current filter</p>
            <p className="text-[10px] text-slate-600 mt-1">Grid operating smoothly</p>
          </div>
        ) : (
          filteredIncidents.map((incident) => (
            <IncidentCard
              key={incident.ticket_id}
              incident={incident}
              onSelect={selectIncident}
              onAcknowledge={handleAcknowledge}
            />
          ))
        )}
      </div>
    </div>
  );
};
