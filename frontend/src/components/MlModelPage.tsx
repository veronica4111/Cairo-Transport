import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Activity, BrainCircuit, Calculator, Database, RefreshCw } from "lucide-react";
import * as api from "../api";
import type { MlCongestionModelResult, MlCongestionPredictionResult } from "../types";

const TIME_OPTIONS = ["morning", "afternoon", "evening", "night"];

function pct(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function numberValue(value: FormDataEntryValue | null, fallback: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export default function MlModelPage() {
  const [model, setModel] = useState<MlCongestionModelResult | null>(null);
  const [prediction, setPrediction] = useState<MlCongestionPredictionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState("");

  const loadModel = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await api.getMlCongestionModel();
      setModel(result);
      setPrediction(null);
    } catch (err) {
      const detail = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(detail.response?.data?.detail || detail.message || "Failed to load ML model");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadModel();
  }, []);

  const chartRows = useMemo(() => model?.sample_predictions.slice(0, 10) || [], [model]);

  const handlePredict = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPredicting(true);
    setError("");
    try {
      const result = await api.predictMlCongestion(
        String(form.get("time_of_day") || "morning"),
        numberValue(form.get("flow"), 1800),
        numberValue(form.get("capacity"), 1500),
        numberValue(form.get("distance"), 6.5)
      );
      setPrediction(result);
    } catch (err) {
      const detail = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(detail.response?.data?.detail || detail.message || "Prediction failed");
    } finally {
      setPredicting(false);
    }
  };

  return (
    <main className="flex-1 overflow-auto bg-bg-primary">
      <div className="mx-auto max-w-7xl px-6 py-6 space-y-5">
        <section className="flex flex-wrap items-center justify-between gap-4 border-b border-border-primary pb-5">
          <div>
            <div className="flex items-center gap-2 text-teal font-mono text-xs tracking-widest">
              <BrainCircuit size={16} />
              CONGESTION PREDICTION
            </div>
            <h1 className="mt-2 text-2xl font-semibold text-text-primary">Machine Learning Model</h1>
          </div>
          <button
            onClick={loadModel}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-md border border-border-primary bg-bg-secondary px-4 py-2 text-xs font-semibold text-text-primary hover:border-teal/50 disabled:opacity-60"
          >
            <RefreshCw size={15} className={loading ? "spinner" : ""} />
            Retrain
          </button>
        </section>

        {error && (
          <div className="rounded-md border border-red/40 bg-red/10 px-4 py-3 text-sm text-red">
            {error}
          </div>
        )}

        {loading && (
          <div className="rounded-md border border-border-primary bg-bg-secondary p-5 text-sm text-text-secondary">
            Training congestion model...
          </div>
        )}

        {model && !loading && (
          <>
            <section className="grid gap-4 md:grid-cols-4">
              <div className="rounded-md border border-border-primary bg-bg-secondary p-4">
                <div className="flex items-center gap-2 text-text-secondary text-xs font-mono">
                  <BrainCircuit size={15} />
                  MODEL
                </div>
                <div className="mt-3 text-xl font-semibold text-text-primary">{model.model_name}</div>
              </div>
              <div className="rounded-md border border-border-primary bg-bg-secondary p-4">
                <div className="flex items-center gap-2 text-text-secondary text-xs font-mono">
                  <Database size={15} />
                  DATASET
                </div>
                <div className="mt-3 text-xl font-semibold text-text-primary">{model.sample_count} rows</div>
                <div className="text-xs text-text-secondary">{model.dataset_origin}</div>
              </div>
              <div className="rounded-md border border-border-primary bg-bg-secondary p-4">
                <div className="flex items-center gap-2 text-text-secondary text-xs font-mono">
                  <Activity size={15} />
                  MSE
                </div>
                <div className="mt-3 text-xl font-semibold text-teal">{model.mse.toFixed(6)}</div>
              </div>
              <div className="rounded-md border border-border-primary bg-bg-secondary p-4">
                <div className="flex items-center gap-2 text-text-secondary text-xs font-mono">
                  <Calculator size={15} />
                  AVG ERROR
                </div>
                <div className="mt-3 text-xl font-semibold text-orange">
                  {model.average_absolute_error.toFixed(4)}
                </div>
              </div>
            </section>

            <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-md border border-border-primary bg-bg-secondary p-4">
                <h2 className="text-sm font-semibold text-text-primary">Actual vs Predicted Congestion</h2>
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full min-w-[520px] text-left text-xs">
                    <thead className="text-text-secondary">
                      <tr className="border-b border-border-primary">
                        <th className="py-2 font-medium">Sample</th>
                        <th className="py-2 font-medium">Actual</th>
                        <th className="py-2 font-medium">Predicted</th>
                        <th className="py-2 font-medium">Absolute Error</th>
                      </tr>
                    </thead>
                    <tbody>
                      {chartRows.map((row) => (
                        <tr key={row.index} className="border-b border-border-primary/60">
                          <td className="py-2 font-mono text-text-secondary">{row.index.toString().padStart(2, "0")}</td>
                          <td className="py-2 text-text-primary">{pct(row.actual)}</td>
                          <td className="py-2 text-teal">{pct(row.predicted)}</td>
                          <td className="py-2 text-orange">{pct(row.absolute_error)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="rounded-md border border-border-primary bg-bg-secondary p-4">
                <h2 className="text-sm font-semibold text-text-primary">Routing Weight Comparison</h2>
                <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded-md bg-bg-primary p-3">
                    <div className="text-text-secondary">Old Formula</div>
                    <div className="mt-2 text-2xl font-semibold text-text-primary">
                      {model.weight_comparison.old_weight.toFixed(4)}
                    </div>
                  </div>
                  <div className="rounded-md bg-bg-primary p-3">
                    <div className="text-text-secondary">ML Weight</div>
                    <div className="mt-2 text-2xl font-semibold text-teal">
                      {model.weight_comparison.ml_weight.toFixed(4)}
                    </div>
                  </div>
                  <div className="rounded-md bg-bg-primary p-3">
                    <div className="text-text-secondary">Static Congestion</div>
                    <div className="mt-2 text-lg text-text-primary">
                      {pct(model.weight_comparison.static_congestion)}
                    </div>
                  </div>
                  <div className="rounded-md bg-bg-primary p-3">
                    <div className="text-text-secondary">ML Prediction</div>
                    <div className="mt-2 text-lg text-teal">
                      {pct(model.weight_comparison.predicted_congestion)}
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-md border border-border-primary bg-bg-secondary p-4">
              <h2 className="text-sm font-semibold text-text-primary">Test A Road Segment</h2>
              <form onSubmit={handlePredict} className="mt-4 grid gap-3 md:grid-cols-5">
                <label className="block">
                  <span className="mb-1.5 block text-[10px] font-semibold tracking-wider text-text-secondary">
                    TIME OF DAY
                  </span>
                  <select
                    name="time_of_day"
                    defaultValue="morning"
                    className="w-full rounded-md border border-border-primary bg-bg-primary px-3 py-2 text-sm text-text-primary outline-none focus:border-teal/60"
                  >
                    {TIME_OPTIONS.map((time) => (
                      <option key={time} value={time}>
                        {time}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-1.5 block text-[10px] font-semibold tracking-wider text-text-secondary">
                    TRAFFIC FLOW
                  </span>
                  <input
                    name="flow"
                    type="number"
                    min="0"
                    defaultValue="1800"
                    className="w-full rounded-md border border-border-primary bg-bg-primary px-3 py-2 text-sm text-text-primary outline-none focus:border-teal/60"
                    placeholder="Vehicles"
                  />
                </label>
                <label className="block">
                  <span className="mb-1.5 block text-[10px] font-semibold tracking-wider text-text-secondary">
                    ROAD CAPACITY
                  </span>
                  <input
                    name="capacity"
                    type="number"
                    min="1"
                    defaultValue="1500"
                    className="w-full rounded-md border border-border-primary bg-bg-primary px-3 py-2 text-sm text-text-primary outline-none focus:border-teal/60"
                    placeholder="Vehicles"
                  />
                </label>
                <label className="block">
                  <span className="mb-1.5 block text-[10px] font-semibold tracking-wider text-text-secondary">
                    DISTANCE KM
                  </span>
                  <input
                    name="distance"
                    type="number"
                    min="0.1"
                    step="0.1"
                    defaultValue="6.5"
                    className="w-full rounded-md border border-border-primary bg-bg-primary px-3 py-2 text-sm text-text-primary outline-none focus:border-teal/60"
                    placeholder="Kilometers"
                  />
                </label>
                <button
                  disabled={predicting}
                  className="mt-[18px] inline-flex items-center justify-center gap-2 rounded-md bg-teal px-4 py-2 text-sm font-semibold text-bg-primary hover:bg-teal/90 disabled:opacity-60"
                >
                  <Calculator size={16} />
                  {predicting ? "Predicting" : "Predict"}
                </button>
              </form>

              {prediction && (
                <div className="mt-4 grid gap-3 md:grid-cols-4">
                  <div className="rounded-md bg-bg-primary p-3">
                    <div className="text-xs text-text-secondary">Predicted Congestion</div>
                    <div className="mt-2 text-xl font-semibold text-teal">
                      {pct(prediction.predicted_congestion)}
                    </div>
                  </div>
                  <div className="rounded-md bg-bg-primary p-3">
                    <div className="text-xs text-text-secondary">Static Congestion</div>
                    <div className="mt-2 text-xl font-semibold text-text-primary">
                      {pct(prediction.static_congestion)}
                    </div>
                  </div>
                  <div className="rounded-md bg-bg-primary p-3">
                    <div className="text-xs text-text-secondary">Old Weight</div>
                    <div className="mt-2 text-xl font-semibold text-text-primary">
                      {prediction.old_weight.toFixed(4)}
                    </div>
                  </div>
                  <div className="rounded-md bg-bg-primary p-3">
                    <div className="text-xs text-text-secondary">ML Weight</div>
                    <div className="mt-2 text-xl font-semibold text-teal">
                      {prediction.ml_weight.toFixed(4)}
                    </div>
                  </div>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}
