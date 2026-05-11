import { useEffect, useMemo, useState } from "react";
import { Download, Pause, Play, RotateCcw, Swords } from "lucide-react";
import * as api from "../api";
import type { NetworkEdge, NetworkNode, RaceResult, RaceStep, RaceTrace, VisualAlgorithm } from "../types";

const TIME_OPTIONS = ["morning", "afternoon", "evening", "night"];
const ALGORITHM_OPTIONS: { value: VisualAlgorithm; label: string }[] = [
  { value: "dijkstra", label: "Dijkstra" },
  { value: "astar", label: "A*" },
  { value: "greedy", label: "Greedy Best-First" },
  { value: "bfs", label: "BFS" },
];

function nodeLabel(node: NetworkNode) {
  return `${node.id} - ${node.name}`;
}

function pathPairs(path: string[]) {
  return new Set(path.slice(0, -1).map((node, index) => [node, path[index + 1]].sort().join("|")));
}

function summarizeStep(step: RaceStep | null, nodes: NetworkNode[]) {
  if (!step) return "No animation step selected.";
  const nodeNames = new Map(nodes.map((node) => [node.id, node.name]));
  const current = nodeNames.get(step.current) || step.current;
  const frontier = step.frontier.slice(0, 5).map((node) => nodeNames.get(node) || node);
  const route = step.path.map((node) => nodeNames.get(node) || node);
  return [
    `Current node: ${current}`,
    `Visited nodes: ${step.visited.length}`,
    `Frontier: ${frontier.length ? frontier.join(", ") : "empty"}`,
    `Current path: ${route.length ? route.join(" -> ") : "not resolved yet"}`,
  ].join("\n");
}

function Legend() {
  const items = [
    ["#4A90E2", "Visited"],
    ["#F5A623", "Frontier/open set"],
    ["#FF4757", "Current node"],
    ["#2ECC71", "Final/current path"],
    ["#8b949e", "Unvisited"],
  ];
  return (
    <div className="flex flex-wrap gap-3 text-xs text-text-secondary">
      {items.map(([color, label]) => (
        <div key={label} className="inline-flex items-center gap-2">
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
          {label}
        </div>
      ))}
    </div>
  );
}

function RacePanel({
  title,
  trace,
  step,
  nodes,
  edges,
}: {
  title: string;
  trace: RaceTrace | null;
  step: RaceStep | null;
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}) {
  const width = 620;
  const height = 390;
  const padding = 34;

  const positions = useMemo(() => {
    if (!nodes.length) return new Map<string, { x: number; y: number; node: NetworkNode }>();
    const lons = nodes.map((node) => node.lon);
    const lats = nodes.map((node) => node.lat);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const lonSpan = maxLon - minLon || 1;
    const latSpan = maxLat - minLat || 1;

    return new Map(
      nodes.map((node) => [
        node.id,
        {
          node,
          x: padding + ((node.lon - minLon) / lonSpan) * (width - padding * 2),
          y: padding + ((maxLat - node.lat) / latSpan) * (height - padding * 2),
        },
      ])
    );
  }, [nodes]);

  const visited = new Set(step?.visited || []);
  const frontier = new Set(step?.frontier || []);
  const activePath = step?.path?.length ? step.path : trace?.final_path || [];
  const pathSet = pathPairs(activePath);
  const pathNodes = new Set(activePath);
  const current = step?.current;

  const metric = (label: string, value: string | number, accent = "text-text-primary") => (
    <div className="rounded-md bg-bg-primary px-3 py-2">
      <div className="text-[10px] font-mono tracking-wider text-text-secondary">{label}</div>
      <div className={`mt-1 text-lg font-semibold ${accent}`}>{value}</div>
    </div>
  );

  return (
    <section className="flex min-h-0 flex-col rounded-md border border-border-primary bg-bg-secondary">
      <div className="flex items-center justify-between border-b border-border-primary px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-text-primary">{title}</h2>
          <div className="text-xs text-text-secondary">{trace?.label || "Waiting for race data"}</div>
        </div>
        <div className="rounded-md bg-bg-primary px-2 py-1 text-xs font-mono text-teal">
          {step ? `STEP ${Math.max(1, step.visited.length)}` : "IDLE"}
        </div>
      </div>

      <div className="min-h-0 flex-1 p-3">
        <svg viewBox={`0 0 ${width} ${height}`} className="h-full min-h-[360px] w-full rounded-md bg-bg-primary">
          {edges
            .filter((edge) => edge.is_existing)
            .map((edge) => {
              const from = positions.get(edge.from_id);
              const to = positions.get(edge.to_id);
              if (!from || !to) return null;
              const key = [edge.from_id, edge.to_id].sort().join("|");
              const inPath = pathSet.has(key);
              return (
                <line
                  key={`${edge.from_id}-${edge.to_id}`}
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke={inPath ? "#2ECC71" : "#30363d"}
                  strokeWidth={inPath ? 5 : 1.5}
                  strokeLinecap="round"
                  opacity={inPath ? 0.95 : 0.75}
                />
              );
            })}

          {nodes.map((node) => {
            const pos = positions.get(node.id);
            if (!pos) return null;
            const isCurrent = current === node.id;
            const color = isCurrent
              ? "#FF4757"
              : pathNodes.has(node.id)
                ? "#2ECC71"
                : frontier.has(node.id)
                  ? "#F5A623"
                  : visited.has(node.id)
                    ? "#4A90E2"
                    : "#8b949e";
            const radius = isCurrent ? 9 : visited.has(node.id) || frontier.has(node.id) ? 7 : 5;
            return (
              <g key={node.id}>
                {isCurrent && <circle cx={pos.x} cy={pos.y} r={15} fill="none" stroke={color} opacity="0.4" />}
                <circle cx={pos.x} cy={pos.y} r={radius} fill={color} stroke="#0d1117" strokeWidth="2" />
                <text x={pos.x + 8} y={pos.y - 8} fill="#e6edf3" fontSize="9" fontFamily="monospace">
                  {node.id}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="grid grid-cols-2 gap-2 border-t border-border-primary p-3 md:grid-cols-4">
        {metric("VISITED", trace?.visited_count ?? "-", "text-blue")}
        {metric("PATH KM", trace?.path_length ?? "-", "text-green")}
        {metric("TIME MS", trace?.execution_time_ms ?? "-", "text-teal")}
        {metric("MEMORY", trace?.memory_units ?? "-", "text-orange")}
      </div>
      <div className="border-t border-border-primary bg-bg-primary/50 p-3">
        <div className="mb-2 text-[10px] font-mono tracking-wider text-text-secondary">STEP EXPLANATION</div>
        <pre className="whitespace-pre-wrap text-xs leading-relaxed text-text-secondary">
          {summarizeStep(step, nodes)}
        </pre>
      </div>
    </section>
  );
}

export default function RaceVisualizerPage({
  nodes,
  edges,
}: {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}) {
  const [algorithmA, setAlgorithmA] = useState<VisualAlgorithm>("dijkstra");
  const [algorithmB, setAlgorithmB] = useState<VisualAlgorithm>("astar");
  const [source, setSource] = useState("");
  const [target, setTarget] = useState("");
  const [timeOfDay, setTimeOfDay] = useState("morning");
  const [speed, setSpeed] = useState(600);
  const [race, setRace] = useState<RaceResult | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (nodes.length && !source) {
      setSource(nodes[0].id);
      setTarget(nodes.find((node) => node.id !== nodes[0].id)?.id || nodes[0].id);
    }
  }, [nodes, source]);

  const maxSteps = race?.summary.step_count || 0;
  const leftStep = race?.left.steps[Math.min(stepIndex, Math.max(0, race.left.steps.length - 1))] || null;
  const rightStep = race?.right.steps[Math.min(stepIndex, Math.max(0, race.right.steps.length - 1))] || null;

  useEffect(() => {
    if (!playing || !race) return;
    if (stepIndex >= maxSteps - 1) {
      setPlaying(false);
      return;
    }
    const timer = window.setTimeout(() => setStepIndex((current) => current + 1), speed);
    return () => window.clearTimeout(timer);
  }, [playing, race, stepIndex, maxSteps, speed]);

  const runRace = async () => {
    if (!source || !target || source === target) {
      setError("Choose two different nodes for source and target.");
      return;
    }
    setLoading(true);
    setError("");
    setPlaying(false);
    try {
      const result = await api.runAlgorithmRace(algorithmA, algorithmB, source, target, timeOfDay);
      setRace(result);
      setStepIndex(0);
      setPlaying(true);
    } catch (err) {
      const detail = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(detail.response?.data?.detail || detail.message || "Race failed");
    } finally {
      setLoading(false);
    }
  };

  const exportSummary = () => {
    if (!race) return;
    const summary = [
      "Algorithm Race Summary",
      `${race.source_name} -> ${race.target_name} at ${race.time_of_day}`,
      `Winner: ${race.summary.winner} (${race.summary.reason})`,
      race.summary.explanation,
      "",
      `${race.left.label}: visited=${race.left.visited_count}, path_km=${race.left.path_length}, time_ms=${race.left.execution_time_ms}, memory=${race.left.memory_units}, path=${race.left.final_path.join(" -> ")}`,
      `${race.right.label}: visited=${race.right.visited_count}, path_km=${race.right.path_length}, time_ms=${race.right.execution_time_ms}, memory=${race.right.memory_units}, path=${race.right.final_path.join(" -> ")}`,
    ].join("\n");
    void navigator.clipboard?.writeText(summary);
    window.alert("Race summary copied to clipboard.");
  };

  return (
    <main className="flex flex-1 flex-col overflow-hidden bg-bg-primary">
      <div className="border-b border-border-primary px-5 py-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="mr-auto">
            <div className="flex items-center gap-2 text-xs font-mono tracking-widest text-teal">
              <Swords size={16} />
              SIDE-BY-SIDE VISUALIZER
            </div>
            <h1 className="mt-1 text-2xl font-semibold text-text-primary">Algorithm Race Animation</h1>
          </div>

          <label className="w-36">
            <span className="mb-1 block text-[10px] font-semibold tracking-wider text-text-secondary">ALGORITHM A</span>
            <select value={algorithmA} onChange={(event) => setAlgorithmA(event.target.value as VisualAlgorithm)} className="w-full rounded-md border border-border-primary bg-bg-secondary px-2 py-2 text-xs text-text-primary">
              {ALGORITHM_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <label className="w-36">
            <span className="mb-1 block text-[10px] font-semibold tracking-wider text-text-secondary">ALGORITHM B</span>
            <select value={algorithmB} onChange={(event) => setAlgorithmB(event.target.value as VisualAlgorithm)} className="w-full rounded-md border border-border-primary bg-bg-secondary px-2 py-2 text-xs text-text-primary">
              {ALGORITHM_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <label className="w-52">
            <span className="mb-1 block text-[10px] font-semibold tracking-wider text-text-secondary">SOURCE</span>
            <select value={source} onChange={(event) => setSource(event.target.value)} className="w-full rounded-md border border-border-primary bg-bg-secondary px-2 py-2 text-xs text-text-primary">
              {nodes.map((node) => <option key={node.id} value={node.id}>{nodeLabel(node)}</option>)}
            </select>
          </label>
          <label className="w-52">
            <span className="mb-1 block text-[10px] font-semibold tracking-wider text-text-secondary">TARGET</span>
            <select value={target} onChange={(event) => setTarget(event.target.value)} className="w-full rounded-md border border-border-primary bg-bg-secondary px-2 py-2 text-xs text-text-primary">
              {nodes.map((node) => <option key={node.id} value={node.id}>{nodeLabel(node)}</option>)}
            </select>
          </label>
          <label className="w-32">
            <span className="mb-1 block text-[10px] font-semibold tracking-wider text-text-secondary">TIME</span>
            <select value={timeOfDay} onChange={(event) => setTimeOfDay(event.target.value)} className="w-full rounded-md border border-border-primary bg-bg-secondary px-2 py-2 text-xs text-text-primary">
              {TIME_OPTIONS.map((time) => <option key={time} value={time}>{time}</option>)}
            </select>
          </label>
          <label className="w-40">
            <span className="mb-1 block text-[10px] font-semibold tracking-wider text-text-secondary">SPEED</span>
            <input type="range" min="120" max="1200" step="60" value={speed} onChange={(event) => setSpeed(Number(event.target.value))} className="w-full accent-teal" />
          </label>
          <button onClick={runRace} disabled={loading} className="inline-flex h-9 items-center gap-2 rounded-md bg-teal px-4 text-sm font-semibold text-bg-primary hover:bg-teal/90 disabled:opacity-60">
            <Play size={16} />
            {loading ? "Loading" : "Start"}
          </button>
          <button onClick={() => setPlaying((value) => !value)} disabled={!race} className="inline-flex h-9 items-center gap-2 rounded-md border border-border-primary bg-bg-secondary px-3 text-sm text-text-primary disabled:opacity-50">
            {playing ? <Pause size={16} /> : <Play size={16} />}
            {playing ? "Pause" : "Play"}
          </button>
          <button onClick={() => { setStepIndex(0); setPlaying(false); }} disabled={!race} className="inline-flex h-9 items-center gap-2 rounded-md border border-border-primary bg-bg-secondary px-3 text-sm text-text-primary disabled:opacity-50">
            <RotateCcw size={16} />
            Reset
          </button>
          <button onClick={exportSummary} disabled={!race} className="inline-flex h-9 items-center gap-2 rounded-md border border-border-primary bg-bg-secondary px-3 text-sm text-text-primary disabled:opacity-50">
            <Download size={16} />
            Export
          </button>
        </div>
        {error && <div className="mt-3 rounded-md border border-red/40 bg-red/10 px-3 py-2 text-sm text-red">{error}</div>}
        <div className="mt-3">
          <Legend />
        </div>
      </div>

      {race && (
        <div className="border-b border-border-primary px-5 py-3 text-sm text-text-secondary">
          <span className="font-semibold text-text-primary">{race.source_name}</span> to{" "}
          <span className="font-semibold text-text-primary">{race.target_name}</span> at {race.time_of_day}. Winner:{" "}
          <span className="font-semibold text-teal">{race.summary.winner}</span> because it {race.summary.reason}.
          <span className="ml-2 text-text-primary">{race.summary.explanation}</span>
        </div>
      )}

      <div className="grid min-h-0 flex-1 gap-4 p-4 xl:grid-cols-2">
        <RacePanel title="Algorithm A" trace={race?.left || null} step={leftStep} nodes={nodes} edges={edges} />
        <RacePanel title="Algorithm B" trace={race?.right || null} step={rightStep} nodes={nodes} edges={edges} />
      </div>
    </main>
  );
}
