import React from 'react';
import { Activity, Gauge, Database } from 'lucide-react';

export const SystemHealthWidget = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Activity className="w-4 h-4 text-emerald-400" />
          Ingestion & Pipeline Health
        </h3>
        <span className="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800/50 px-2 py-0.5 rounded font-mono">
          HEALTHY
        </span>
      </div>

      <div className="space-y-2.5 text-xs">
        <div className="flex justify-between items-center bg-slate-950/60 px-3 py-2 rounded-lg border border-slate-800">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Gauge className="w-3.5 h-3.5 text-blue-400" /> Steady Throughput
          </span>
          <span className="font-mono text-slate-200 font-bold">39 msg/s</span>
        </div>

        <div className="flex justify-between items-center bg-slate-950/60 px-3 py-2 rounded-lg border border-slate-800">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-amber-400" /> Burst Tolerance
          </span>
          <span className="font-mono text-slate-200 font-bold">5,000 msgs / 10s</span>
        </div>
      </div>
    </div>
  );
};
