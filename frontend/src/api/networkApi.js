import axiosClient from './axiosClient';

export const networkApi = {
  fetchSubstations: () => axiosClient.get('/network/substations/'),
  fetchFeeders: () => axiosClient.get('/network/feeders/'),
  fetchTransformers: () => axiosClient.get('/network/transformers/'),
  fetchPoles: (dtId) => axiosClient.get(`/network/poles/?dt_id=${dtId}`),
};
