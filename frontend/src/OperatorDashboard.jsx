import { useState } from "react";

export default function OperatorDashboard({ incidents, onRefresh }) {
  const [feedTab, setFeedTab] = useState("active"); // "active" | "closed"
  const [assigningId, setAssigningId] = useState(null);
  const [crewName, setCrewName] = useState("");
  const [actionLoading, setActionLoading] = useState(null);
  const [message, setMessage] = useState(null);

  async function handleAcknowledge(incidentId) {
    setActionLoading(incidentId);
    setMessage(null);
    try {
      const res = await fetch(`/api/incidents/${incidentId}/acknowledge/`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to acknowledge incident");
      setMessage({ type: "success", text: `Incident #${incidentId} acknowledged.` });
      onRefresh();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setActionLoading(null);
    }
  }

  async function handleAssignCrew(incidentId) {
    if (!crewName.trim()) return;
    setActionLoading(incidentId);
    setMessage(null);
    try {
      const res = await fetch(`/api/incidents/${incidentId}/assign/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ crew_name: crewName.trim() })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to assign crew");
      setMessage({ type: "success", text: `Crew '${crewName}' assigned to Incident #${incidentId}.` });
      setAssigningId(null);
      setCrewName("");
      onRefresh();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setActionLoading(null);
    }
  }

  async function handleReportRepair(incidentId) {
    setActionLoading(incidentId);
    setMessage(null);
    try {
      const res = await fetch(`/api/incidents/${incidentId}/repair-reported/`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to report repair");
      setMessage({ type: "success", text: `Repair reported for Incident #${incidentId}. Awaiting telemetry verification.` });
      onRefresh();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setActionLoading(null);
    }
  }

  async function handleSimulateRepair(incidentId) {
    setActionLoading(incidentId);
    setMessage(null);
    try {
      const res = await fetch(`/api/simulator/incidents/${incidentId}/repair/`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to simulate restoration");
      setMessage({ type: "success", text: `Restoration telemetry verified! Incident #${incidentId} moved to VERIFIED & CLOSED.` });
      onRefresh();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setActionLoading(null);
    }
  }

  const activeIncidents = incidents.filter(i => i.status !== "closed" && i.status !== "verified");
  const closedIncidents = incidents.filter(i => i.status === "closed" || i.status === "verified");
  const displayedIncidents = feedTab === "active" ? activeIncidents : closedIncidents;

  const statusBadge = (status) => {
    switch (status) {
      case "detected":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800">Detected</span>;
      case "acknowledged":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">Acknowledged</span>;
      case "crew_assigned":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800">Crew Assigned</span>;
      case "repair_reported":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800">Repair Reported (Awaiting Telemetry)</span>;
      case "verified":
      case "closed":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">✓ Verified & Closed</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  const confidenceBadge = (confidence) => {
    if (confidence === "high") return <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-1 rounded border border-emerald-200">High Confidence</span>;
    if (confidence === "medium") return <span className="text-xs font-bold text-amber-700 bg-amber-50 px-2 py-1 rounded border border-amber-200">Medium Confidence</span>;
    return <span className="text-xs font-bold text-slate-600 bg-slate-100 px-2 py-1 rounded border border-slate-200">Low Confidence</span>;
  };

  return (
    <section className="space-y-6">
      {/* Header Metrics */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <button onClick={() => setFeedTab("active")} className={`rounded-xl border p-4 text-left transition ${feedTab === "active" ? "border-red-500 bg-red-50/50 ring-2 ring-red-400" : "border-slate-200 bg-white"}`}>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Outages</p>
          <p className="mt-2 text-3xl font-extrabold text-red-600">{activeIncidents.length}</p>
        </button>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Needs Acknowledgment</p>
          <p className="mt-2 text-3xl font-extrabold text-amber-600">{incidents.filter(i => i.status === "detected").length}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Crews Deployed</p>
          <p className="mt-2 text-3xl font-extrabold text-blue-600">{incidents.filter(i => i.status === "crew_assigned").length}</p>
        </div>
        <button onClick={() => setFeedTab("closed")} className={`rounded-xl border p-4 text-left transition ${feedTab === "closed" ? "border-emerald-500 bg-emerald-50/50 ring-2 ring-emerald-400" : "border-slate-200 bg-white"}`}>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Verified & Closed</p>
          <p className="mt-2 text-3xl font-extrabold text-emerald-600">{closedIncidents.length}</p>
        </button>
      </div>

      {message && (
        <div className={`p-4 rounded-xl text-sm font-medium ${message.type === "success" ? "bg-emerald-50 text-emerald-800 border border-emerald-200" : "bg-red-50 text-red-800 border border-red-200"}`}>
          {message.text}
        </div>
      )}

      {/* Incidents Section */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-100 pb-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              {feedTab === "active" ? "Active Outage Feed" : "Verified & Closed Incidents Archive"}
            </h2>
            <p className="text-xs text-slate-500">
              {feedTab === "active" ? "Live active tickets requiring operator attention." : "Historical tickets verified via restoration telemetry."}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex rounded-lg bg-slate-100 p-1 text-xs font-bold">
              <button
                onClick={() => setFeedTab("active")}
                className={`rounded-md px-3 py-1.5 transition ${feedTab === "active" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-900"}`}
              >
                Active Outages ({activeIncidents.length})
              </button>
              <button
                onClick={() => setFeedTab("closed")}
                className={`rounded-md px-3 py-1.5 transition ${feedTab === "closed" ? "bg-white text-emerald-800 shadow-sm" : "text-slate-500 hover:text-slate-900"}`}
              >
                Closed Archive ({closedIncidents.length})
              </button>
            </div>
            <button onClick={onRefresh} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100">
              Refresh
            </button>
          </div>
        </div>

        {displayedIncidents.length === 0 ? (
          <div className="py-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
              ✓
            </div>
            <h3 className="mt-3 text-sm font-bold text-slate-900">
              {feedTab === "active" ? "No Active Outages" : "No Closed Incidents Yet"}
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              {feedTab === "active" ? "Grid is operating normally across all feeders." : "Closed incidents will appear here once telemetry verifies restoration."}
            </p>
          </div>
        ) : (
          <div className="mt-4 divide-y divide-slate-100">
            {displayedIncidents.map((incident) => (
              <div key={incident.id} className="py-5 first:pt-2">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-3">
                      <span className="text-base font-extrabold text-slate-950">Incident #{incident.id}</span>
                      {statusBadge(incident.status)}
                      {confidenceBadge(incident.confidence)}
                    </div>
                    <p className="text-sm font-semibold text-slate-800">
                      Fault Type: <span className="capitalize text-red-600">{incident.fault_type.replace("_", " ")}</span>
                    </p>
                    <p className="text-xs text-slate-600">
                      <span className="font-semibold">Asset:</span> Feeder: {incident.feeder_id || "N/A"} | DT: {incident.transformer_id || "N/A"}
                      {incident.upstream_pole_id && ` | Line Span: ${incident.upstream_pole_id} → ${incident.downstream_pole_id}`}
                    </p>
                    <p className="text-xs text-slate-500">
                      <span className="font-semibold">Coordinates:</span> {incident.latitude}, {incident.longitude} | <span className="font-semibold">PIN:</span> {incident.pincode || "560078"}
                    </p>
                    <p className="mt-2 rounded-lg bg-slate-50 p-2.5 text-xs text-slate-700 border border-slate-200">
                      <span className="font-semibold text-slate-900">Diagnosis:</span> {incident.confidence_reason}
                    </p>
                  </div>

                  <div className="flex flex-col items-end gap-2 text-right">
                    <div className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-bold text-white">
                      {incident.affected_pole_count} Poles Affected
                    </div>
                    <span className="text-[11px] text-slate-400">
                      Detected: {new Date(incident.detected_at).toLocaleTimeString()}
                    </span>

                    {/* Workflow Actions */}
                    <div className="mt-3 flex flex-wrap gap-2 justify-end">
                      {incident.status === "detected" && (
                        <button
                          disabled={actionLoading === incident.id}
                          onClick={() => handleAcknowledge(incident.id)}
                          className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-amber-700 disabled:opacity-50"
                        >
                          Acknowledge
                        </button>
                      )}

                      {incident.status === "acknowledged" && (
                        assigningId === incident.id ? (
                          <div className="flex items-center gap-1.5">
                            <input
                              type="text"
                              placeholder="Crew name (e.g. Line Unit 4)"
                              value={crewName}
                              onChange={(e) => setCrewName(e.target.value)}
                              className="rounded-lg border border-slate-300 px-2 py-1 text-xs"
                            />
                            <button
                              onClick={() => handleAssignCrew(incident.id)}
                              className="rounded-lg bg-blue-600 px-2.5 py-1 text-xs font-bold text-white hover:bg-blue-700"
                            >
                              Save
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setAssigningId(incident.id)}
                            className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-blue-700"
                          >
                            Assign Crew
                          </button>
                        )
                      )}

                      {incident.status === "crew_assigned" && (
                        <button
                          disabled={actionLoading === incident.id}
                          onClick={() => handleReportRepair(incident.id)}
                          className="rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-purple-700 disabled:opacity-50"
                        >
                          Mark Repair Complete
                        </button>
                      )}

                      {incident.status === "repair_reported" && (
                        <button
                          disabled={actionLoading === incident.id}
                          onClick={() => handleSimulateRepair(incident.id)}
                          className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-50"
                        >
                          Simulate Restoration Telemetry
                        </button>
                      )}

                      {(incident.status === "closed" || incident.status === "verified") && (
                        <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
                          ✓ Verified & Closed ({new Date(incident.closed_at || incident.verified_at || Date.now()).toLocaleTimeString()})
                        </span>
                      )}
                    </div>
                    {incident.assigned_crew && (
                      <p className="mt-1 text-xs text-blue-700 font-semibold">Assigned: {incident.assigned_crew}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
