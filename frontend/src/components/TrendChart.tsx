import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";
import type { YearMetrics } from "../api/client";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

type Props = {
  years: YearMetrics[];
};

export function TrendChart({ years }: Props) {
  const data = {
    labels: years.map((y) => String(y.year)),
    datasets: [
      {
        label: "Heatwave events / year",
        data: years.map((y) => y.event_count),
        borderColor: "#c45c26",
        backgroundColor: "rgba(196, 92, 38, 0.15)",
        tension: 0.25,
        pointRadius: 2,
      },
      {
        label: "5-year rolling mean",
        data: years.map((y) => y.rolling_mean_5yr),
        borderColor: "#1f4e5f",
        borderDash: [6, 4],
        tension: 0.25,
        pointRadius: 0,
        spanGaps: true,
      },
    ],
  };

  return (
    <section className="panel chart-panel">
      <header className="panel-header">
        <h2>Frequency over time</h2>
        <p>Events of 3+ consecutive days above the regional 95th-percentile Tmax.</p>
      </header>
      <div className="chart-wrap">
        <Line
          data={data}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: "top" },
            },
            scales: {
              y: {
                beginAtZero: true,
                title: { display: true, text: "Events" },
                ticks: { precision: 0 },
              },
              x: {
                title: { display: true, text: "Year" },
              },
            },
          }}
        />
      </div>
    </section>
  );
}
