import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import { useApp } from '../../context/AppContext';
import { networkApi } from '../../api/networkApi';

// Fix Leaflet marker icon asset URLs in React SPA
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const dtIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export const NetworkMap = () => {
  const { incidents, selectIncident } = useApp();
  const [poles, setPoles] = useState([]);
  const [dtPosition, setDtPosition] = useState([12.9678, 77.5951]);

  useEffect(() => {
    networkApi.fetchPoles('D-0112')
      .then((data) => {
        const poleList = data.results || data || [];
        setPoles(poleList);
        if (poleList.length > 0) {
          setDtPosition([parseFloat(poleList[0].latitude), parseFloat(poleList[0].longitude)]);
        }
      })
      .catch(() => {
        // Fallback default poles for map display if API unpopulated
        setPoles([
          { pole_id: 'P-024431', latitude: 12.968214, longitude: 77.594612, seq_on_line: 1 },
          { pole_id: 'P-024432', latitude: 12.968901, longitude: 77.594330, seq_on_line: 2 },
          { pole_id: 'P-024433', latitude: 12.969455, longitude: 77.593980, seq_on_line: 3 }
        ]);
      });
  }, []);

  // Collect active fault span polylines
  const faultSpans = incidents
    .filter(i => i.status !== 'closed' && i.latitude && i.longitude)
    .map(i => ({
      ticket_id: i.ticket_id,
      from_pole: i.from_pole_id,
      to_pole: i.to_pole_id,
      position: [parseFloat(i.latitude), parseFloat(i.longitude)],
      asset_type: i.asset_type
    }));

  return (
    <div className="h-full w-full relative bg-slate-950">
      <MapContainer
        center={dtPosition}
        zoom={16}
        scrollWheelZoom={true}
        className="h-full w-full z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Transformer Marker */}
        <Marker position={dtPosition} icon={dtIcon}>
          <Popup>
            <div className="text-slate-900 text-xs">
              <strong>Distribution Transformer D-0112</strong><br />
              Feeder F-07-03 • 250 kVA
            </div>
          </Popup>
        </Marker>

        {/* Poles Markers */}
        {poles.map((pole) => (
          <CircleMarker
            key={pole.pole_id}
            center={[parseFloat(pole.latitude), parseFloat(pole.longitude)]}
            radius={5}
            pathOptions={{
              color: '#3b82f6',
              fillColor: '#1d4ed8',
              fillOpacity: 0.8,
              weight: 2
            }}
          >
            <Popup>
              <div className="text-slate-900 text-xs font-mono">
                <strong>Pole {pole.pole_id}</strong><br />
                Seq: {pole.seq_on_line || 'Inferred'}<br />
                Device: {pole.device_id || 'None'}
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* Fault Span Overlays (Pulsing Red Markers) */}
        {faultSpans.map((fs) => (
          <CircleMarker
            key={fs.ticket_id}
            center={fs.position}
            radius={12}
            pathOptions={{
              color: '#ef4444',
              fillColor: '#dc2626',
              fillOpacity: 0.6,
              weight: 3
            }}
            eventHandlers={{
              click: () => selectIncident(fs.ticket_id)
            }}
          >
            <Popup>
              <div className="text-slate-900 text-xs">
                <strong className="text-rose-600">FAULT BOUNDARY LOCATION</strong><br />
                Span: {fs.from_pole} → {fs.to_pole}<br />
                Click to open detail panel
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
};
