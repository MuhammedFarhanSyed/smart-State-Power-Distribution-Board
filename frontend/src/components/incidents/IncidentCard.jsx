import React from 'react';
import { AlertOctagon, MapPin, Users, CheckCircle, Clock } from 'lucide-react';

export const IncidentCard = ({ incident, onSelect, onAcknowledge }) => {
  const isDetected = incident.status === 'detected';
  const isClosed = incident.status === 'closed';

  const statusColors = {
    detected: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
    acknowledged: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    crew_assigned: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    resolved: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    verified: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    closed: 'bg-slate-800 text-slate-400 border-slate-700',
  };

  return (
    <div
      onClick={() => onSelect(incident.ticket_id)}
      className={`bg-slate-900 border rounded-xl p-4 cursor-pointer transition-all hover:border-blue-500/50 hover:shadow-md ${
        isDetected ? 'border-rose-500/40 bg-rose-950/10' : 'border-slate-800'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <AlertOctagon className="w-4 h-4" />
          </span>
          <div>
            <h4 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
              {incident.asset_type === 'span' ? (
                <>Span Break: <span className="text-amber-400 font-mono">{incident.from_pole_id} → {incident.to_pole_id}</span></>
              ) : (
                <>Transformer Outage: <span className="text-amber-400 font-mono">{incident.dt_id}</span></>
              )}
            </h4>
            <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
              <MapPin className="w-3 h-3 text-slate-500" />
              <span>DT {incident.dt_id} • Feeder {incident.feeder_id}</span>
              {incident.pincode && <span className="text-slate-500">• PIN {incident.pincode}</span>}
            </div>
          </div>
        </div>

        <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${statusColors[incident.status] || 'bg-slate-800'}`}>
          {incident.status.replace('_', ' ')}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 py-2 border-y border-slate-800/80 my-3 text-center text-xs">
        <div>
          <div className="text-[10px] text-slate-500 uppercase font-semibold">Affected Poles</div>
          <div className="font-mono font-bold text-slate-200 mt-0.5 flex items-center justify-center gap-1">
            <Users className="w-3 h-3 text-blue-400" /> {incident.affected_poles_count}
          </div>
        </div>

        <div>
          <div className="text-[10px] text-slate-500 uppercase font-semibold">Confidence</div>
          <div className="font-mono font-bold text-emerald-400 mt-0.5">
            {Math.round(incident.confidence_score * 100)}%
          </div>
        </div>

        <div>
          <div className="text-[10px] text-slate-500 uppercase font-semibold">Crew</div>
          <div className="font-semibold text-slate-300 truncate mt-0.5">
            {incident.assigned_crew || 'Unassigned'}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-1">
        <span className="text-[10px] text-slate-400 flex items-center gap-1">
          <Clock className="w-3 h-3 text-slate-500" />
          {new Date(incident.detected_at).toLocaleTimeString()}
        </span>

        {isDetected && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAcknowledge(incident.ticket_id);
            }}
            className="bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-bold px-3 py-1 rounded-lg transition-colors"
          >
            Acknowledge
          </button>
        )}
      </div>
    </div>
  );
};
