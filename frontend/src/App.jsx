import { useEffect, useMemo, useState } from "react";
import OperatorDashboard from "./OperatorDashboard";

const network = [
  {
    feederId: "F-07-01",
    transformers: [
      { id: "D-0001", poles: ["P-000002", "P-000003", "P-000004", "P-000005", "P-000006"] },
      { id: "D-0004", poles: ["P-000242", "P-000243", "P-000244", "P-000245", "P-000246"] }
    ]
  },
  {
    feederId: "F-07-02",
    transformers: [
      { id: "D-0002", poles: ["P-000082", "P-000083", "P-000084", "P-000085", "P-000086"] },
      { id: "D-0005", poles: ["P-000322", "P-000323", "P-000324", "P-000325", "P-000326"] }
    ]
  },
  {
    feederId: "F-07-03",
    transformers: [
      { id: "D-0003", poles: ["P-000162", "P-000163", "P-000164", "P-000165", "P-000166"] },
      { id: "D-0006", poles: ["P-000402", "P-000403", "P-000404", "P-000405", "P-000406"] }
    ]
  }
];

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

function App() {
  const [activeTab, setActiveTab] = useState("dashboard"); // "dashboard" | "simulator"
  const [incidents, setIncidents] = useState([]);
  const [selection, setSelection] = useState(null);
  const [result, setResult] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch live incidents from Django backend
  async function fetchIncidents() {
    try {
      const response = await fetch(`${API_BASE}/api/incidents/`);
      if (response.ok) {
        const data = await response.json();
        setIncidents(data);
      }
    } catch (err) {
      console.error("Failed to fetch incidents:", err);
    }
  }

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 4000);
    return () => clearInterval(interval);
  }, []);

  const selectionText = useMemo(() => {
    if (!selection) return "Choose a feeder, transformer, or pole/span to simulate a fault.";
    if (selection.type === "feeder") return `Feeder fault: ${selection.feederId}`;
    if (selection.type === "transformer") return `Transformer fault: ${selection.dtId}`;
    return `Span fault upstream of ${selection.downstreamPoleId} at ${selection.dtId}`;
  }, [selection]);

  function isDark(feederId, dtId, poleId, poleIndex) {
    if (!selection) return false;
    if (selection.type === "feeder") return selection.feederId === feederId;
    if (selection.type === "transformer") return selection.dtId === dtId;
    return selection.dtId === dtId && poleIndex >= selection.poleIndex;
  }

  function toggleSelection(nextSelection, matchesCurrentSelection) {
    setSelection(matchesCurrentSelection ? null : nextSelection);
    setResult(null);
  }

  async function createAlert() {
    if (!selection) return;
    setIsSubmitting(true);
    setResult(null);
    const payload = selection.type === "feeder"
      ? { fault_type: "feeder", feeder_id: selection.feederId }
      : selection.type === "transformer"
        ? { fault_type: "transformer", dt_id: selection.dtId }
        : { fault_type: "span", downstream_pole_id: selection.downstreamPoleId };

    try {
      const response = await fetch(`${API_BASE}/api/simulator/faults/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "The backend rejected the simulated fault.");
      setResult({ kind: "success", text: `Alert sent: ${data.telemetry_messages_sent} telemetry messages created for ${data.affected_poles} poles.` });
      await fetchIncidents();
      setTimeout(() => setActiveTab("dashboard"), 600);
    } catch (error) {
      setResult({ kind: "error", text: error.message });
    } finally {
      setIsSubmitting(false);
    }
  }

  const activeIncidentsCount = incidents.filter(i => i.status !== "closed" && i.status !== "verified").length;

  return (
    <main className="min-h-screen bg-slate-50 p-6 md:p-10">
      <section className="mx-auto max-w-6xl">
        <header className="mb-8 flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <p className="text-xs font-bold tracking-widest text-blue-700 uppercase">KSPDB Outage Control System</p>
              <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-800">Live</span>
            </div>
            <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-950">Karnataka Distribution Console</h1>
            <p className="mt-1 text-sm text-slate-600">Smart State Power Distribution Board — Ingestion, Localization & Operator Dispatch</p>
          </div>

          <div className="flex items-center gap-3">
            <nav className="flex rounded-xl bg-slate-200 p-1">
              <button
                onClick={() => setActiveTab("dashboard")}
                className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-bold transition ${activeTab === "dashboard" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
              >
                Control Room
                {activeIncidentsCount > 0 && (
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-red-600 text-[10px] text-white">
                    {activeIncidentsCount}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab("simulator")}
                className={`rounded-lg px-4 py-2 text-xs font-bold transition ${activeTab === "simulator" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
              >
                Fault Simulator
              </button>
            </nav>
            <div className="hidden rounded-xl bg-slate-900 px-3 py-2 text-xs text-slate-200 md:block">
              Backend: <span className="font-semibold text-emerald-400">127.0.0.1:8000</span>
            </div>
          </div>
        </header>

        {activeTab === "dashboard" ? (
          <OperatorDashboard incidents={incidents} onRefresh={fetchIncidents} />
        ) : (
          <div className="grid gap-6 lg:grid-cols-[1fr_330px]">
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Distribution Network Assets</h2>
                  <p className="text-xs text-slate-500">Click a Feeder, DT, or Pole Span to preview power loss and send telemetry.</p>
                </div>
              </div>

              <div className="mt-6 grid gap-5 md:grid-cols-3">
                {network.map((feeder) => (
                  <div key={feeder.feederId} className={`rounded-xl border p-4 ${selection?.type === "feeder" && selection.feederId === feeder.feederId ? "border-red-400 bg-red-50" : "border-slate-200"}`}>
                    <button onClick={() => toggleSelection({ type: "feeder", feederId: feeder.feederId }, selection?.type === "feeder" && selection.feederId === feeder.feederId)} className="w-full rounded-lg bg-blue-700 px-3 py-2 text-left font-bold text-white hover:bg-blue-800">
                      {feeder.feederId}
                      <span className="mt-1 block text-xs font-normal text-blue-100">Click for feeder fault</span>
                    </button>

                    <div className="mx-auto h-5 w-1 bg-slate-300" />
                    <div className="space-y-5">
                      {feeder.transformers.map((transformer) => (
                        <div key={transformer.id}>
                          <button onClick={() => toggleSelection({ type: "transformer", feederId: feeder.feederId, dtId: transformer.id }, selection?.type === "transformer" && selection.dtId === transformer.id)} className={`w-full rounded-lg px-3 py-2 text-left font-semibold ring-1 transition ${isDark(feeder.feederId, transformer.id) ? "bg-slate-800 text-white ring-slate-800" : "bg-amber-100 text-amber-950 ring-amber-300 hover:bg-amber-200"}`}>
                            DT · {transformer.id}
                          </button>
                          <div className="ml-6 border-l-2 border-slate-300 pl-4 pt-3">
                            {transformer.poles.map((pole, index) => {
                              const dark = isDark(feeder.feederId, transformer.id, pole, index);
                              return (
                                <button key={pole} onClick={() => toggleSelection({ type: "span", feederId: feeder.feederId, dtId: transformer.id, downstreamPoleId: pole, poleIndex: index }, selection?.type === "span" && selection.downstreamPoleId === pole)} className="group flex w-full items-center gap-2 py-1 text-left">
                                  <span className={`h-3 w-3 rounded-full ring-4 ${dark ? "bg-slate-950 ring-slate-300" : "bg-emerald-500 ring-emerald-100"}`} />
                                  <span className={`text-sm font-medium ${dark ? "text-slate-900" : "text-slate-600"}`}>{pole}</span>
                                  <span className="ml-auto text-xs text-slate-400 opacity-0 group-hover:opacity-100">fault here</span>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Selected Simulation Target</p>
              <p className="mt-3 min-h-16 text-base font-bold text-slate-900">{selectionText}</p>
              <button disabled={!selection || isSubmitting} onClick={createAlert} className="mt-5 w-full rounded-xl bg-red-600 px-4 py-3 font-bold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-slate-300">
                {isSubmitting ? "Sending Telemetry Alert…" : "Inject Fault Alert"}
              </button>
              <p className="mt-3 text-xs leading-5 text-slate-500">This sends raw telemetry to `/api/simulator/faults/`. The Django localization engine analyzes signals and creates the ticket in the Control Room.</p>
              {result && <p className={`mt-5 rounded-lg p-3 text-xs font-semibold ${result.kind === "success" ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"}`}>{result.text}</p>}
            </aside>
          </div>
        )}
      </section>
    </main>
  );
}

export default App;
