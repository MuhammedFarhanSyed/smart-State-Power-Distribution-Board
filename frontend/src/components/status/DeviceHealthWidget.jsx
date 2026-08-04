import React from 'react';
import { Cpu, WifiOff, CheckCircle } from 'lucide-react';

export const DeviceHealthWidget = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Cpu className="w-4 h-4 text-blue-400" />
          IoT Device Fleet Health
        </h3>
        <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">34,900 Fitted</span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
          <div className="text-sm font-bold text-emerald-400 flex items-center justify-center gap-1">
            <CheckCircle className="w-3.5 h-3.5" /> 96%
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Active Online</div>
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
          <div className="text-sm font-bold text-rose-400 flex items-center justify-center gap-1">
            <WifiOff className="w-3.5 h-3.5" /> ~4%
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Offline / Sensor Drop</div>
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
          <div className="text-sm font-bold text-amber-400">~8%</div>
          <div className="text-[10px] text-slate-400 mt-0.5">FW 1.2 Quiet Mode</div>
        </div>
      </div>
    </div>
  );
};
