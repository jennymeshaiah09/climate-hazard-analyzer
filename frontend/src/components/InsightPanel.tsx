import type { AnalyzeResponse } from "../api/client";

type Props = {
  result: AnalyzeResponse;
};

export function InsightPanel({ result }: Props) {
  return (
    <section className="panel insight-panel">
      <header className="panel-header">
        <h2>Insight</h2>
        <p>
          Threshold P95 = <strong>{result.threshold_c.toFixed(1)}°C</strong>
          {result.cached ? " · served from cache" : ""}
        </p>
      </header>
      <p className="insight-text">{result.insight}</p>
      <dl className="stat-grid">
        <div>
          <dt>Trend</dt>
          <dd>{result.trend.direction}</dd>
        </div>
        <div>
          <dt>Slope / decade</dt>
          <dd>{result.trend.slope_per_decade.toFixed(2)}</dd>
        </div>
        <div>
          <dt>R²</dt>
          <dd>{result.trend.r_squared.toFixed(2)}</dd>
        </div>
        <div>
          <dt>Sample events</dt>
          <dd>{result.events_sample.length}</dd>
        </div>
      </dl>
      <p className="muted source">{result.data_source}</p>
    </section>
  );
}
