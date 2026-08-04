import React from 'react';
import { AlertCircle, Zap, ShieldCheck } from 'lucide-react';

export const StatisticsWidget = ({ incidents = [] }) => {
  const spanFaults = incidents.filter(i => i.asset_type === 'span' && i.status !== 'closed').length;
  const dtFaults = incidents.filter(i => i.asset_type === 'dt' && i.status !== 'closed').length;
  const closedCount = incidents.filter(i => i.status === 'closed').length;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
        <AlertCircle className="w-4 h-4 text-rose-400" />
        Fault Breakdown
      </h3>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
          <div className="text-base font-bold text-rose-400">{spanFaults}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Span Breaks</div>
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
          <div className="text-base font-bold text-amber-400">{dtFaults}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">DT Outages</div>
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
          <div className="text-base font-bold text-emerald-400">{closedCount}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Verified Closed</div>
        </div>
      </div>
    </div>
  );
};
