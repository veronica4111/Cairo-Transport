import { useCallback, useEffect, useState } from "react";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import MapView from "./components/MapView";
import BottomMetrics from "./components/BottomMetrics";
import MlModelPage from "./components/MlModelPage";
import RaceVisualizerPage from "./components/RaceVisualizerPage";
import ToastContainer, { type ToastMessage } from "./components/Toast";
import type {
  NetworkNode,
  NetworkEdge,
  NetworkSummary,
  AlgorithmType,
  AlgorithmResult,
  SystemLog,
} from "./types";
import * as api from "./api";

let logId = 0;
let toastId = 0;

function requireString(params: Record<string, unknown>, key: string): string {
  const value = params[key];
  if (typeof value !== "string") {
    throw new Error(`Invalid parameter: ${key}`);
  }
  return value;
}

function requireNumber(params: Record<string, unknown>, key: string): number {
  const value = params[key];
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new Error(`Invalid parameter: ${key}`);
  }
  return value;
}

function requireStringArray(params: Record<string, unknown>, key: string): string[] {
  const value = params[key];
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string")) {
    throw new Error(`Invalid parameter: ${key}`);
  }
  return value;
}

export default function App() {
  const [activeTab, setActiveTab] = useState("NETWORK MAP");
  const [nodes, setNodes] = useState<NetworkNode[]>([]);
  const [edges, setEdges] = useState<NetworkEdge[]>([]);
  const [summary, setSummary] = useState<NetworkSummary | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [algorithmResult, setAlgorithmResult] = useState<AlgorithmResult | null>(null);
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addLog = useCallback(
    (message: string, type: SystemLog["type"] = "info") => {
      setLogs((prev) => [...prev, { id: ++logId, message, type, timestamp: Date.now() }]);
    },
    []
  );

  const addToast = useCallback(
    (message: string, type: ToastMessage["type"] = "info") => {
      setToasts((prev) => [...prev, { id: ++toastId, message, type }]);
    },
    []
  );

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Load initial data
  useEffect(() => {
    const load = async () => {
      try {
        addLog("Initializing network data...");
        const [nodeData, edgeData, summaryData] = await Promise.all([
          api.getNetworkNodes(),
          api.getNetworkEdges(),
          api.getNetworkSummary(),
        ]);
        setNodes(nodeData);
        setEdges(edgeData);
        setSummary(summaryData);
        addLog(
          `Loaded ${nodeData.length} nodes, ${edgeData.length} edges`,
          "success"
        );
      } catch (err) {
        const error = err as { response?: { data?: { detail?: string } }, message?: string };
        addLog(`Failed to load network data: ${error.message || "Unknown error"}`, "error");
        addToast("Failed to connect to backend. Is the API running?", "error");
      }
    };
    load();
  }, [addLog, addToast]);

  // Run algorithm
  const handleRunAlgorithm = useCallback(
    async (type: AlgorithmType, params: Record<string, unknown>) => {
      setIsRunning(true);
      addLog(`Running ${type}...`);

      try {
        let data: unknown;
        switch (type) {
          case "shortest-path":
            data = await api.runShortestPath(
              requireString(params, "source"),
              requireString(params, "target"),
              requireString(params, "time_of_day")
            );
            break;
          case "emergency-routing":
            data = await api.runEmergencyRouting(requireString(params, "incident_node"));
            break;
          case "mst":
            data = await api.runMST();
            break;
          case "bus-allocation":
            data = await api.runBusAllocation(requireNumber(params, "budget"));
            break;
          case "road-maintenance":
            data = await api.runRoadMaintenance(requireNumber(params, "budget"));
            break;
          case "traffic-signals":
            data = await api.runTrafficSignals(
              requireString(params, "node_id"),
              requireString(params, "time_of_day")
            );
            break;
          case "memoized-planner":
            data = await api.runMemoizedPlanner(
              requireString(params, "source"),
              requireStringArray(params, "destinations"),
              requireString(params, "time_of_day")
            );
            break;
          case "rush-hour":
            data = await api.runRushHour(requireString(params, "time_of_day"));
            break;
          case "road-closure":
            data = await api.runRoadClosure(
              requireString(params, "from_node"),
              requireString(params, "to_node")
            );
            break;
          case "new-road-analysis":
            data = await api.runNewRoadAnalysis();
            break;
          default:
            throw new Error(`Unknown algorithm: ${type}`);
        }

        setAlgorithmResult({ type, data, timestamp: Date.now() });
        addLog(`${type} completed successfully`, "success");
        addToast(`${type.replace(/-/g, " ")} completed`, "success");
      } catch (err) {
        const error = err as { response?: { data?: { detail?: string } }, message?: string };
        const detail =
          error.response?.data?.detail || error.message || "Unknown error";
        addLog(`Error: ${detail}`, "error");
        addToast(`Algorithm failed: ${detail}`, "error");
      } finally {
        setIsRunning(false);
      }
    },
    [addLog, addToast]
  );

  return (
    <div className="flex flex-col h-screen bg-bg-primary text-text-primary overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-bg-tertiary via-bg-primary to-bg-primary">
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === "ML MODEL" ? (
        <MlModelPage />
      ) : activeTab === "RACE VIEW" ? (
        <RaceVisualizerPage nodes={nodes} edges={edges} />
      ) : (
        <div className="flex flex-1 overflow-hidden relative">
          <Sidebar
            nodes={nodes}
            onRunAlgorithm={handleRunAlgorithm}
            isRunning={isRunning}
            result={algorithmResult}
            logs={logs}
          />

          <div className="flex flex-col flex-1 overflow-hidden relative">
            {/* We position the map absolute to take full space, 
                then BottomMetrics floats on top */}
            <div className="absolute inset-0">
              <MapView
                nodes={nodes}
                edges={edges}
                algorithmResult={algorithmResult}
              />
            </div>
            
            <div className="absolute bottom-0 left-0 right-0 z-[1001] pointer-events-none">
              <div className="pointer-events-auto">
                <BottomMetrics summary={summary} />
              </div>
            </div>
          </div>
        </div>
      )}

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}
