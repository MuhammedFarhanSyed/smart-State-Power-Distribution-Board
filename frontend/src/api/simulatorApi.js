import axiosClient from './axiosClient';

export const simulatorApi = {
  loadNetwork: (dtId = 'D-0112') => axiosClient.post('/simulator/load-network', { dt_id: dtId }),
  startSimulation: (dtId = 'D-0112') => axiosClient.post('/simulator/start', { dt_id: dtId }),
  stopSimulation: () => axiosClient.post('/simulator/stop'),
  resetSimulation: () => axiosClient.post('/simulator/reset'),
  injectSpanFault: (dtId, fromPoleId, toPoleId, applyNoise = true) => axiosClient.post('/simulator/fault/span', {
    dt_id: dtId,
    from_pole_id: fromPoleId,
    to_pole_id: toPoleId,
    apply_noise: applyNoise
  }),
  injectTransformerFault: (dtId, applyNoise = True) => axiosClient.post('/simulator/fault/transformer', {
    dt_id: dtId,
    apply_noise: applyNoise
  }),
  injectFeederFault: (feederId, dtIds, applyNoise = True) => axiosClient.post('/simulator/fault/feeder', {
    feeder_id: feederId,
    dt_ids: dtIds,
    apply_noise: applyNoise
  }),
  repairFault: (faultId) => axiosClient.post(`/simulator/repair/${faultId}`),
  fetchSimulatorStatus: () => axiosClient.get('/simulator/status'),
};
