import React from 'react';
import { Clock, User, CheckCircle2, AlertCircle } from 'lucide-react';

export const Timeline = ({ timeline = [] }) => {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="text-xs text-slate-500 italic py-2">
        No status transitions recorded yet.
      </div>
    );
  }

  return (
    <div className="space-y-4 relative before:absolute before:inset-0 before:left-2.5 before:w-0.5 before:bg-slate-800">
      {timeline.map((event, idx) => (
        <div key={idx} className="relative flex items-start space-x-3 pl-6">
          <div className="absolute left-1 top-1 -translate-x-1/2 w-3 h-3 rounded-full bg-slate-900 border-2 border-blue-500"></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 w-full text-xs">
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-slate-200 uppercase font-mono tracking-wider">
                {event.from_status ? `${event.from_status} → ${event.to_status}` : event.to_status}
              </span>
              <span className="text-[10px] text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(event.timestamp).toLocaleTimeString()}
              </span>
            </div>

            <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mb-1">
              <User className="w-3 h-3 text-slate-500" />
              <span>{event.changed_by}</span>
            </div>

            {event.notes && (
              <p className="text-[11px] text-slate-300 bg-slate-950/60 p-2 rounded border border-slate-800/80 font-sans mt-2">
                {event.notes}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
