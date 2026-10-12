import { useEffect, useMemo, useState } from "react";
import { MapContainer, Marker, Rectangle, TileLayer, useMapEvents } from "react-leaflet";
import L from "leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import { geocode, type GeocodeResult } from "../api/client";

// Fix default Leaflet marker paths under Vite
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

export type RegionSelection = {
  lat: number;
  lon: number;
  label: string;
  north?: number;
  south?: number;
  east?: number;
  west?: number;
};

type Props = {
  value: RegionSelection;
  onChange: (region: RegionSelection) => void;
};

function MapClickHandler({
  boxMode,
  onPoint,
  onBoxCorner,
}: {
  boxMode: boolean;
  onPoint: (lat: number, lon: number) => void;
  onBoxCorner: (lat: number, lon: number) => void;
}) {
  useMapEvents({
    click(e) {
      if (boxMode) onBoxCorner(e.latlng.lat, e.latlng.lng);
      else onPoint(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export function RegionPicker({ value, onChange }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GeocodeResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [boxMode, setBoxMode] = useState(false);
  const [boxStart, setBoxStart] = useState<{ lat: number; lon: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    const handle = window.setTimeout(async () => {
      setSearching(true);
      setError(null);
      try {
        setResults(await geocode(query.trim()));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Geocoding failed");
        setResults([]);
      } finally {
        setSearching(false);
      }
    }, 350);
    return () => window.clearTimeout(handle);
  }, [query]);

  const bounds = useMemo(() => {
    if (
      value.north != null &&
      value.south != null &&
      value.east != null &&
      value.west != null
    ) {
      return [
        [value.south, value.west] as [number, number],
        [value.north, value.east] as [number, number],
      ];
    }
    return null;
  }, [value]);

  function selectResult(item: GeocodeResult) {
    setBoxMode(false);
    setBoxStart(null);
    onChange({ lat: item.lat, lon: item.lon, label: item.label });
    setQuery(item.label);
    setResults([]);
  }

  function handlePoint(lat: number, lon: number) {
    onChange({
      lat: Number(lat.toFixed(4)),
      lon: Number(lon.toFixed(4)),
      label: `Point ${lat.toFixed(2)}, ${lon.toFixed(2)}`,
    });
  }

  function handleBoxCorner(lat: number, lon: number) {
    if (!boxStart) {
      setBoxStart({ lat, lon });
      return;
    }
    const north = Math.max(boxStart.lat, lat);
    const south = Math.min(boxStart.lat, lat);
    const east = Math.max(boxStart.lon, lon);
    const west = Math.min(boxStart.lon, lon);
    const centerLat = (north + south) / 2;
    const centerLon = (east + west) / 2;
    onChange({
      lat: Number(centerLat.toFixed(4)),
      lon: Number(centerLon.toFixed(4)),
      label: `Box ${south.toFixed(2)}–${north.toFixed(2)}N, ${west.toFixed(2)}–${east.toFixed(2)}E`,
      north: Number(north.toFixed(4)),
      south: Number(south.toFixed(4)),
      east: Number(east.toFixed(4)),
      west: Number(west.toFixed(4)),
    });
    setBoxStart(null);
  }

  return (
    <section className="panel region-picker">
      <header className="panel-header">
        <h2>Region</h2>
        <p>Search a city or click the map. Box mode uses the bbox center for analysis.</p>
      </header>

      <div className="search-row">
        <input
          type="search"
          placeholder="Search city or state…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search location"
        />
        <button
          type="button"
          className={boxMode ? "toggle active" : "toggle"}
          onClick={() => {
            setBoxMode((v) => !v);
            setBoxStart(null);
          }}
        >
          {boxMode ? "Box mode on" : "Draw box"}
        </button>
      </div>

      {searching && <p className="muted">Searching…</p>}
      {error && <p className="error">{error}</p>}
      {results.length > 0 && (
        <ul className="search-results">
          {results.map((item) => (
            <li key={`${item.label}-${item.lat}-${item.lon}`}>
              <button type="button" onClick={() => selectResult(item)}>
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="map-wrap">
        <MapContainer
          center={[value.lat, value.lon]}
          zoom={5}
          scrollWheelZoom
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler boxMode={boxMode} onPoint={handlePoint} onBoxCorner={handleBoxCorner} />
          <Marker position={[value.lat, value.lon]} />
          {bounds && <Rectangle bounds={bounds} pathOptions={{ color: "#c45c26", weight: 2 }} />}
        </MapContainer>
      </div>

      <p className="selection-meta">
        Selected: <strong>{value.label}</strong> ({value.lat.toFixed(2)}, {value.lon.toFixed(2)})
        {boxMode && boxStart && " — click opposite corner to finish box"}
      </p>
    </section>
  );
}
