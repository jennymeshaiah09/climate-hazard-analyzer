type Props = {
  startYear: number;
  endYear: number;
  loading: boolean;
  onStartYear: (y: number) => void;
  onEndYear: (y: number) => void;
  onAnalyze: () => void;
};

export function Controls({
  startYear,
  endYear,
  loading,
  onStartYear,
  onEndYear,
  onAnalyze,
}: Props) {
  return (
    <section className="panel controls">
      <header className="panel-header">
        <h2>Analysis</h2>
        <p>Heatwave is fixed for this assessment build.</p>
      </header>

      <label className="field">
        <span>Hazard</span>
        <select value="heatwave" disabled aria-label="Hazard type">
          <option value="heatwave">Heatwave</option>
        </select>
      </label>

      <div className="year-row">
        <label className="field">
          <span>Start year</span>
          <input
            type="number"
            min={1940}
            max={2024}
            value={startYear}
            onChange={(e) => onStartYear(Number(e.target.value))}
          />
        </label>
        <label className="field">
          <span>End year</span>
          <input
            type="number"
            min={1940}
            max={2024}
            value={endYear}
            onChange={(e) => onEndYear(Number(e.target.value))}
          />
        </label>
      </div>

      <button type="button" className="primary" disabled={loading} onClick={onAnalyze}>
        {loading ? "Analyzing…" : "Analyze heatwaves"}
      </button>
    </section>
  );
}
