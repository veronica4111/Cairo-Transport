import axios from "axios";
import type {
  NetworkNode,
  NetworkEdge,
  NetworkSummary,
  DbSummary,
  ShortestPathResult,
  EmergencyResult,
  MSTResult,
  BusAllocationResult,
  RoadMaintenanceResult,
  TrafficSignalsResult,
  MemoizedPlannerResult,
  RushHourResult,
  RoadClosureResult,
  NewRoadAnalysisResult,
  MlCongestionModelResult,
  MlCongestionPredictionResult,
  RaceResult,
  VisualAlgorithm,
} from "./types";

const api = axios.create({ baseURL: "/api" });

/* ─── Network ─── */
export const getNetworkSummary = () =>
  api.get<NetworkSummary>("/network/summary").then((r) => r.data);

export const getNetworkNodes = () =>
  api.get<NetworkNode[]>("/network/nodes").then((r) => r.data);

export const getNetworkEdges = () =>
  api.get<NetworkEdge[]>("/network/edges").then((r) => r.data);

/* ─── DB ─── */
export const getDbSummary = () =>
  api.get<DbSummary>("/db/summary").then((r) => r.data);

export const getDemandPairs = () =>
  api.get("/db/demand-pairs").then((r) => r.data);

export const getDbContents = () =>
  api.get("/db/all-contents").then((r) => r.data);

/* ─── Algorithms ─── */
export const runShortestPath = (source: string, target: string, time_of_day: string) =>
  api
    .post<ShortestPathResult>("/algorithms/shortest-path", { source, target, time_of_day })
    .then((r) => r.data);

export const runEmergencyRouting = (incident_node: string) =>
  api
    .post<EmergencyResult>("/algorithms/emergency-routing", { incident_node })
    .then((r) => r.data);

export const runMST = () =>
  api.post<MSTResult>("/algorithms/mst").then((r) => r.data);

export const runBusAllocation = (budget: number) =>
  api
    .post<BusAllocationResult>("/algorithms/bus-allocation", { budget })
    .then((r) => r.data);

export const runRoadMaintenance = (budget: number) =>
  api
    .post<RoadMaintenanceResult>("/algorithms/road-maintenance", { budget })
    .then((r) => r.data);

export const runTrafficSignals = (node_id: string, time_of_day: string) =>
  api
    .post<TrafficSignalsResult>("/algorithms/traffic-signals", { node_id, time_of_day })
    .then((r) => r.data);

export const runMemoizedPlanner = (
  source: string,
  destinations: string[],
  time_of_day: string
) =>
  api
    .post<MemoizedPlannerResult>("/algorithms/memoized-planner", {
      source,
      destinations,
      time_of_day,
    })
    .then((r) => r.data);

/* ─── Simulations ─── */
export const runRushHour = (time_of_day: string) =>
  api
    .post<RushHourResult>("/simulation/rush-hour", { time_of_day })
    .then((r) => r.data);

export const runRoadClosure = (from_node: string, to_node: string) =>
  api
    .post<RoadClosureResult>("/simulation/road-closure", { from_node, to_node })
    .then((r) => r.data);

export const runNewRoadAnalysis = () =>
  api.post<NewRoadAnalysisResult>("/simulation/new-road-analysis").then((r) => r.data);

/* Machine learning */
export const getMlCongestionModel = () =>
  api.get<MlCongestionModelResult>("/ml/congestion-model").then((r) => r.data);

export const predictMlCongestion = (
  time_of_day: string,
  flow: number,
  capacity: number,
  distance: number
) =>
  api
    .post<MlCongestionPredictionResult>("/ml/predict-congestion", {
      time_of_day,
      flow,
      capacity,
      distance,
    })
    .then((r) => r.data);

/* Visualization */
export const runAlgorithmRace = (
  algorithm_a: VisualAlgorithm,
  algorithm_b: VisualAlgorithm,
  source: string,
  target: string,
  time_of_day: string
) =>
  api
    .post<RaceResult>("/visualization/race", {
      algorithm_a,
      algorithm_b,
      source,
      target,
      time_of_day,
    })
    .then((r) => r.data);
