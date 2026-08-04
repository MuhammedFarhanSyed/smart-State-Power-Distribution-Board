import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { incidentApi } from '../api/incidentApi';
import { simulatorApi } from '../api/simulatorApi';

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [simulatorStatus, setSimulatorStatus] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'detail' | 'simulator'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const fetchIncidents = useCallback(async () => {
    try {
      setError(null);
      const data = await incidentApi.fetchIncidents();
      setIncidents(data.results || []);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch incidents:', err);
      setError('Unable to fetch incidents from control room server.');
    }
  }, []);

  const fetchSimulatorStatus = useCallback(async () => {
    try {
      const data = await simulatorApi.fetchSimulatorStatus();
      setSimulatorStatus(data);
    } catch (err) {
      // Simulator status fetch error silently handled if offline
    }
  }, []);

  // Poll every 30 seconds
  useEffect(() => {
    setLoading(true);
    Promise.all([fetchIncidents(), fetchSimulatorStatus()]).finally(() => setLoading(false));

    const interval = setInterval(() => {
      fetchIncidents();
      fetchSimulatorStatus();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchIncidents, fetchSimulatorStatus]);

  const selectIncident = async (ticketId) => {
    try {
      setLoading(true);
      const detail = await incidentApi.fetchIncidentById(ticketId);
      setSelectedIncident(detail);
      setActiveTab('detail');
    } catch (err) {
      setError(`Failed to load incident detail for ${ticketId}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (ticketId) => {
    try {
      await incidentApi.acknowledgeIncident(ticketId);
      await fetchIncidents();
      if (selectedIncident?.ticket_id === ticketId) {
        await selectIncident(ticketId);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAssignCrew = async (ticketId, crewName, notes) => {
    try {
      await incidentApi.assignCrew(ticketId, crewName, notes);
      await fetchIncidents();
      if (selectedIncident?.ticket_id === ticketId) {
        await selectIncident(ticketId);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleMarkResolved = async (ticketId, notes) => {
    try {
      const res = await incidentApi.markResolved(ticketId, notes);
      await fetchIncidents();
      if (selectedIncident?.ticket_id === ticketId) {
        await selectIncident(ticketId);
      }
      return res;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  return (
    <AppContext.Provider
      value={{
        incidents,
        selectedIncident,
        simulatorStatus,
        activeTab,
        setActiveTab,
        loading,
        error,
        lastUpdated,
        fetchIncidents,
        fetchSimulatorStatus,
        selectIncident,
        handleAcknowledge,
        handleAssignCrew,
        handleMarkResolved,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
