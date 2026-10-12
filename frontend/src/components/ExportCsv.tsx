import type { AnalyzeResponse } from "../api/client";

type Props = {
  result: AnalyzeResponse;
};

export function ExportCsv({ result }: Props) {
  function download() {
    const header = [
      "year",
      "event_count",
      "mean_duration",
      "mean_intensity",
      "hot_day_count",
      "rolling_mean_5yr",
      "low_confidence",
    ];
    const rows = result.years.map((y) =>
      [
        y.year,
        y.event_count,
        y.mean_duration ?? "",
        y.mean_intensity ?? "",
        y.hot_day_count,
        y.rolling_mean_5yr ?? "",
        y.low_confidence,
      ].join(","),
    );
    const meta = [
      `# region,${result.region.label ?? ""}`,
      `# lat,${result.region.lat}`,
      `# lon,${result.region.lon}`,
      `# threshold_c,${result.threshold_c}`,
      `# insight,${JSON.stringify(result.insight)}`,
    ];
    const csv = [...meta, header.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const slug = (result.region.label || "region").replace(/[^a-z0-9]+/gi, "_").slice(0, 40);
    a.href = url;
    a.download = `heatwave_${slug}_${result.years[0]?.year}-${result.years.at(-1)?.year}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <button type="button" className="secondary" onClick={download}>
      Export CSV
    </button>
  );
}
