import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { Timeline } from './Timeline';
import { ShieldCheck, UserCheck, Wrench, Navigation, AlertTriangle, Layers } from 'lucide-react';

export const IncidentDetailPanel = () => {
  const { selectedIncident, handleAcknowledge, handleAssignCrew, handleMarkResolved } = useApp();
  const [crewName, setCrewName] = useState('');
  const [assignNotes, setAssignNotes] = useState('');
  const [resolveNotes, setResolveNotes] = useState('');
  const [message, setMessage] = useState(null);

  if (!selectedIncident) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center text-slate-500">
        <AlertTriangle className="w-10 h-10 text-slate-700 mb-3" />
        <h3 className="text-sm font-semibold text-slate-400">No Incident Selected</h3>
        <p className="text-xs text-slate-600 mt-1 max-w-sm">
          Select an active incident from the dashboard feed to review location coordinates, primary fault boundary, and dispatch controls.
        </p>
      </div>
    );
  }

  const {
    ticket_id,
    asset_type,
    feeder_id,
    dt_id,
    from_pole_id,
    to_pole_id,
    latitude,
    longitude,
    pincode,
    affected_poles_count,
    confidence_score,
    confidence_reasons,
    assigned_crew,
    status,
    detected_at,
    affected_poles = [],
    timeline = []
  } = selectedIncident;

  const onAssign = async (e) => {
    e.preventDefault();
    if (!crewName.trim()) return;
    await handleAssignCrew(ticket_id, crewName, assignNotes);
    setCrewName('');
    setAssignNotes('');
  };

  const onResolve = async (e) => {
    e.preventDefault();
    try {
      const res = await handleMarkResolved(ticket_id, resolveNotes);
      setMessage(res.verification_details);
      setResolveNotes('');
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-slate-950 p-6 space-y-6">
      {/* Header Info */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-blue-400 bg-blue-950/80 border border-blue-800/60 px-2 py-0.5 rounded">
                TICKET #{ticket_id.slice(0, 8)}
              </span>
              <span className="text-xs font-bold uppercase tracking-wider text-rose-400 bg-rose-950/60 border border-rose-800/60 px-2.5 py-0.5 rounded">
                {asset_type.toUpperCase()} FAULT
              </span>
            </div>
            <h2 className="text-lg font-bold text-slate-100 mt-2">
              {asset_type === 'span' ? `Wire Span Break: ${from_pole_id} → ${to_pole_id}` : `DT Outage ${dt_id}`}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Detected at {new Date(detected_at).toLocaleString()}
            </p>
          </div>

          <div className="text-right">
            <span className="text-xs font-bold uppercase px-3 py-1 rounded-lg border bg-slate-800 text-slate-200">
              {status.replace('_', ' ')}
            </span>
          </div>
        </div>

        {/* Coordinates & Navigation Link */}
        <div className="mt-4 pt-4 border-t border-slate-800/80 grid grid-cols-3 gap-4 text-xs">
          <div>
            <span className="text-slate-500 text-[10px] uppercase font-semibold">GPS Dispatch Coords</span>
            <div className="font-mono font-bold text-slate-200 mt-0.5 flex items-center gap-1">
              <Navigation className="w-3.5 h-3.5 text-blue-400" />
              {latitude}, {longitude}
            </div>
          </div>

          <div>
            <span className="text-slate-500 text-[10px] uppercase font-semibold">PIN Code</span>
            <div className="font-mono font-bold text-slate-200 mt-0.5">
              {pincode || 'Unavailable'}
            </div>
          </div>

          <div>
            <span className="text-slate-500 text-[10px] uppercase font-semibold">Assigned Crew</span>
            <div className="font-semibold text-slate-200 mt-0.5">
              {assigned_crew || 'Unassigned'}
            </div>
          </div>
        </div>
      </div>

      {/* Operator Workflow Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
          <Wrench className="w-4 h-4 text-amber-400" />
          Operator Workflow Action Panel
        </h3>

        {message && (
          <div className="mb-4 p-3 rounded-lg bg-blue-950/80 border border-blue-800 text-xs text-blue-200 font-mono">
            {message}
          </div>
        )}

        {status === 'detected' && (
          <button
            onClick={() => handleAcknowledge(ticket_id)}
            className="w-full bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs py-2.5 rounded-lg transition-colors"
          >
            Acknowledge Incident Ticket
          </button>
        )}

        {status === 'acknowledged' && (
          <form onSubmit={onAssign} className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Repair Crew / Vehicle Name</label>
              <input
                type="text"
                value={crewName}
                onChange={(e) => setCrewName(e.target.value)}
                placeholder="e.g. Lineman Van #04 (Ramesh & Team)"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Dispatch Notes</label>
              <input
                type="text"
                value={assignNotes}
                onChange={(e) => setAssignNotes(e.target.value)}
                placeholder="e.g. Equipped with 9m PCC ladder and 11kV LT wire spool"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-lg transition-colors"
            >
              Assign Crew & Dispatch
            </button>
          </form>
        )}

        {status === 'crew_assigned' && (
          <form onSubmit={onResolve} className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Field Repair Notes</label>
              <input
                type="text"
                value={resolveNotes}
                onChange={(e) => setResolveNotes(e.target.value)}
                placeholder="e.g. Wire re-spliced at Pole P3. Power restored."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <ShieldCheck className="w-4 h-4" />
              Mark Resolved (Triggers Telemetry Auto-Verification)
            </button>
          </form>
        )}

        {(status === 'resolved' || status === 'verified' || status === 'closed') && (
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-400">
            <span className="text-emerald-400 font-bold">Ticket is in telemetry verification stage.</span>
            <p className="text-[11px] text-slate-500 mt-1">
              Note: Manual closure is disabled. System will auto-close ticket when field sensors confirm 100% power restoration.
            </p>
          </div>
        )}
      </div>

      {/* Diagnostics & Confidence Audit */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Localization Confidence Audit ({Math.round(confidence_score * 100)}%)
        </h3>
        <ul className="space-y-1.5 text-xs text-slate-300">
          {confidence_reasons.map((reason, idx) => (
            <li key={idx} className="flex items-start gap-2 bg-slate-950/60 p-2 rounded border border-slate-800/80">
              <span className="text-emerald-400">•</span>
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Affected Poles List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-400" />
          Grouped Downstream Dark Poles ({affected_poles_count})
        </h3>
        <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto p-1">
          {affected_poles.map((ap) => (
            <span
              key={ap.pole_id}
              className={`text-xs font-mono px-2.5 py-1 rounded border ${
                ap.is_boundary
                  ? 'bg-rose-950/80 border-rose-800 text-rose-300 font-bold'
                  : 'bg-slate-950 border-slate-800 text-slate-300'
              }`}
            >
              {ap.pole_id} {ap.is_boundary && '(Boundary Edge)'}
            </span>
          ))}
        </div>
      </div>

      {/* Audit Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-4">
          Incident Audit Timeline
        </h3>
        <Timeline timeline={timeline} />
      </div>
    </div>
  );
};
