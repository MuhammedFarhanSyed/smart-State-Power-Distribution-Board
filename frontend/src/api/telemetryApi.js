import axiosClient from './axiosClient';

export const telemetryApi = {
  ingestTelemetry: (payload) => axiosClient.post('/telemetry/', payload),
};
