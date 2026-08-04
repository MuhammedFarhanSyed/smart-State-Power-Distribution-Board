import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { simulatorApi } from '../../api/simulatorApi';
import { Play, Square, RotateCcw, Zap, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';

export const SimulatorControlPanel = () => {
  const { simulatorStatus, fetchSimulatorStatus, fetchIncidents } = useApp();
  const [dtId, setDtId] = useState('D-0112');
  const [fromPole, setFromPole] = useState('P-024431');
  const [toPole, setToPole] = useState('P-024432');
  const [applyNoise, setApplyNoise] = useState(true);
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAction = async (actionFn, successMsg) => {
    try {
      setLoading(true);
      setMsg(null);
      const res = await actionFn();
      setMsg(res.message || successMsg);
      await fetchSimulatorStatus();
      await fetchIncidents();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-slate-950 p-6 space-y-6">
      {/* Session Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              Grid Telemetry & Fault Simulator
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Simulate realistic field Blackout events, capacitor packet drops, and FW 1.2 quiet fleet mode.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleAction(() => simulatorApi.startSimulation(dtId), "Simulation started.")}
              disabled={loading}
              className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5" /> Start
            </button>

            <button
              onClick={() => handleAction(() => simulatorApi.stopSimulation(), "Simulation stopped.")}
              disabled={loading}
              className="bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5"
            >
              <Square className="w-3.5 h-3.5" /> Stop
            </button>

            <button
              onClick={() => handleAction(() => simulatorApi.resetSimulation(), "Workspace reset.")}
              disabled={loading}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Reset
            </button>
          </div>
        </div>

        {msg && (
          <div className="p-3 rounded-lg bg-blue-950/80 border border-blue-800 text-xs text-blue-200 font-mono mb-3">
            {msg}
          </div>
        )}

        <div className="flex items-center gap-4 text-xs bg-slate-950 p-3 rounded-lg border border-slate-800">
          <button
            onClick={() => handleAction(() => simulatorApi.loadNetwork(dtId), "Network tree loaded.")}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-3 py-1.5 rounded transition-colors flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> Load Network Tree
          </button>

          <label className="flex items-center gap-2 text-slate-300">
            <input
              type="checkbox"
              checked={applyNoise}
              onChange={(e) => setApplyNoise(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-blue-600"
            />
            <span>Apply 30% Dying Packet Loss & FW 1.2 Quiet Mode Noise</span>
          </label>
        </div>
      </div>

      {/* Fault Injection Options */}
      <div className="grid grid-cols-2 gap-6">
        {/* Inject Span Fault */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            Inject Span Wire Break
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">DT ID</label>
              <input
                type="text"
                value={dtId}
                onChange={(e) => setDtId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Upstream Live Pole (From Pole)</label>
              <input
                type="text"
                value={fromPole}
                onChange={(e) => setFromPole(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Downstream Dark Pole (To Pole)</label>
              <input
                type="text"
                value={toPole}
                onChange={(e) => setToPole(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
              />
            </div>

            <button
              onClick={() => handleAction(() => simulatorApi.injectSpanFault(dtId, fromPole, toPole, applyNoise), "Span fault injected.")}
              disabled={loading}
              className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold py-2.5 rounded-lg transition-colors"
            >
              Inject Wire Span Break
            </button>
          </div>
        </div>

        {/* Inject DT / Feeder Outages */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            Inject Major Equipment Outages
          </h3>

          <div className="space-y-3 text-xs">
            <button
              onClick={() => handleAction(() => simulatorApi.injectTransformerFault(dtId, applyNoise), "DT fault injected.")}
              disabled={loading}
              className="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold py-2.5 rounded-lg transition-colors text-left px-4 flex items-center justify-between"
            >
              <span>Inject Transformer (DT) Outage</span>
              <span className="font-mono text-[10px] bg-slate-950/60 px-2 py-1 rounded">{dtId}</span>
            </button>

            <button
              onClick={() => handleAction(() => simulatorApi.injectFeederFault('F-07-03', ['D-0112', 'D-0113'], applyNoise), "Feeder fault injected.")}
              disabled={loading}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2.5 rounded-lg transition-colors text-left px-4 flex items-center justify-between"
            >
              <span>Inject 11kV Feeder Outage</span>
              <span className="font-mono text-[10px] bg-slate-950/60 px-2 py-1 rounded">F-07-03</span>
            </button>
          </div>
        </div>
      </div>

      {/* Active Injected Faults & Repair Stream */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-400" />
          Active Injected Faults & Field Restoration ({simulatorStatus?.active_faults_count || 0})
        </h3>

        {!simulatorStatus?.active_faults || simulatorStatus.active_faults.length === 0 ? (
          <div className="text-xs text-slate-500 italic py-4 text-center">
            No active injected faults running in the simulator.
          </div>
        ) : (
          <div className="space-y-2">
            {simulatorStatus.active_faults.map((f) => (
              <div key={f.fault_id} className="flex items-center justify-between bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                <div>
                  <span className="font-bold text-slate-200 uppercase font-mono">{f.fault_type} FAULT</span>
                  <span className="text-slate-400 ml-2">Target: {f.target_id}</span>
                  {f.span && <span className="text-amber-400 font-mono ml-2">({f.span})</span>}
                </div>

                <button
                  onClick={() => handleAction(() => simulatorApi.repairFault(f.fault_id), "Power restored & telemetry stream injected.")}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-3 py-1.5 rounded transition-colors text-xs"
                >
                  Repair & Restore Power
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
