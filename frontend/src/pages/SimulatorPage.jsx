import React from 'react';
import { SimulatorControlPanel } from '../components/simulator/SimulatorControlPanel';

export const SimulatorPage = () => {
  return (
    <div className="h-full w-full bg-slate-950 overflow-hidden">
      <SimulatorControlPanel />
    </div>
  );
};
