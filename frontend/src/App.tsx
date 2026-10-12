import { useState } from "react";
import { analyze, type AnalyzeResponse } from "./api/client";
import { Controls } from "./components/Controls";
import { ExportCsv } from "./components/ExportCsv";
import { InsightPanel } from "./components/InsightPanel";
import { RegionPicker, type RegionSelection } from "./components/RegionPicker";
import { TrendChart } from "./components/TrendChart";
import "./App.css";

const DEFAULT_REGION: RegionSelection = {
  lat: 28.6139,
  lon: 77.209,
  label: "New Delhi, India",
};

export default function App() {
  const [region, setRegion] = useState<RegionSelection>(DEFAULT_REGION);
  const [startYear, setStartYear] = useState(1990);
  const [endYear, setEndYear] = useState(2020);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        lat: region.lat,
        lon: region.lon,
        start_year: startYear,
        end_year: endYear,
        label: region.label,
        ...(region.north != null &&
          region.south != null &&
          region.east != null &&
          region.west != null && {
            north: region.north,
            south: region.south,
            east: region.east,
            west: region.west,
          }),
      };
      const data = await analyze(payload);
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="hero">
        <p className="brand">Climate Hazard Trend Analyzer</p>
        <h1>Heatwave trends for a place you choose</h1>
        <p className="lede">
          Historical daily maxima from Open-Meteo, scored with a 3-day / 95th-percentile heatwave
          definition.
        </p>
      </header>

      <main className="layout">
        <aside className="sidebar">
          <RegionPicker value={region} onChange={setRegion} />
          <Controls
            startYear={startYear}
            endYear={endYear}
            loading={loading}
            onStartYear={setStartYear}
            onEndYear={setEndYear}
            onAnalyze={handleAnalyze}
          />
          {result && <ExportCsv result={result} />}
        </aside>

        <div className="results">
          {error && <p className="error banner">{error}</p>}
          {!result && !error && !loading && (
            <p className="placeholder">Pick a region and year range, then analyze.</p>
          )}
          {loading && <p className="placeholder">Fetching weather and detecting heatwaves…</p>}
          {result && (
            <>
              <InsightPanel result={result} />
              <TrendChart years={result.years} />
            </>
          )}
        </div>
      </main>

      <footer className="footer">
        <span>Dygnify case study build · Heatwave-only scope</span>
      </footer>
    </div>
  );
}
