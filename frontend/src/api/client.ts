const API_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || "http://localhost:8000";

export type GeocodeResult = {
  name: string | null;
  country: string | null;
  admin1: string | null;
  lat: number;
  lon: number;
  label: string;
};

export type YearMetrics = {
  year: number;
  event_count: number;
  mean_duration: number | null;
  mean_intensity: number | null;
  hot_day_count: number;
  low_confidence: boolean;
  missing_fraction: number;
  rolling_mean_5yr: number | null;
};

export type AnalyzeResponse = {
  region: {
    lat: number;
    lon: number;
    label: string | null;
    bbox: { north: number; south: number; east: number; west: number } | null;
  };
  hazard: string;
  threshold_c: number;
  years: YearMetrics[];
  trend: {
    slope_per_year: number;
    slope_per_decade: number;
    r_squared: number;
    p_value: number;
    direction: string;
  };
  insight: string;
  cached: boolean;
  events_sample: Array<{
    start: string;
    end: string;
    duration_days: number;
    mean_intensity: number;
    peak_tmax: number;
  }>;
  data_source: string;
};

export type AnalyzePayload = {
  lat: number;
  lon: number;
  start_year: number;
  end_year: number;
  label?: string;
  north?: number;
  south?: number;
  east?: number;
  west?: number;
  hazard?: "heatwave";
};

async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join("; ");
    }
    return JSON.stringify(data);
  } catch {
    return res.statusText || "Request failed";
  }
}

export async function geocode(q: string): Promise<GeocodeResult[]> {
  const res = await fetch(`${API_URL}/api/geocode?q=${encodeURIComponent(q)}`);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function analyze(payload: AnalyzePayload): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, hazard: "heatwave" }),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export { API_URL };
