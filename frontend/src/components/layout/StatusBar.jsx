import React from 'react';
import { useApp } from '../../context/AppContext';
import { Radio, Zap, AlertTriangle, CheckCircle2 } from 'lucide-react';

export const StatusBar = () => {
  const { incidents } = useApp();
  const activeCount = incidents.filter(i => i.status !== 'closed').length;
  const criticalCount = incidents.filter(i => i.status === 'detected').length;

  return (
    <div className="bg-slate-900 border-t border-slate-800 px-6 py-2 flex items-center justify-between text-xs text-slate-400">
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>Substation SD-07: <strong>4 Substations</strong> / <strong>31 Feeders</strong> / <strong>412 DTs</strong></span>
        </div>
        <span className="text-slate-800">|</span>
        <div className="flex items-center space-x-2">
          <Radio className="w-3.5 h-3.5 text-blue-400" />
          <span>IoT Fleet: <strong>34,900 Devices (~91% fitted)</strong> • Steady Stream <strong>39 msg/s</strong></span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {criticalCount > 0 ? (
          <div className="flex items-center space-x-1.5 text-rose-400 bg-rose-950/40 border border-rose-800/40 px-2.5 py-0.5 rounded-full">
            <AlertTriangle className="w-3.5 h-3.5 animate-pulse" />
            <span className="font-semibold">{criticalCount} Unacknowledged Fault(s) Require Attention</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-0.5 rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Grid Operating Normally</span>
          </div>
        )}
      </div>
    </div>
  );
};
