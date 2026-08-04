import axiosClient from './axiosClient';

export const incidentApi = {
  fetchIncidents: (params = {}) => axiosClient.get('/incidents/', { params }),
  fetchIncidentById: (ticketId) => axiosClient.get(`/incidents/${ticketId}/`),
  acknowledgeIncident: (ticketId) => axiosClient.patch(`/incidents/${ticketId}/acknowledge/`),
  assignCrew: (ticketId, crewName, notes = '') => axiosClient.patch(`/incidents/${ticketId}/assign/`, { crew_name: crewName, notes }),
  markResolved: (ticketId, notes = '') => axiosClient.patch(`/incidents/${ticketId}/resolve/`, { notes }),
};
