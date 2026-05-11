/* ─── Node & Edge types matching the backend ─── */

export interface NetworkNode {
  id: string;
  name: string;
  population: number;
  node_type: string;
  lon: number;
  lat: number;
  connected_roads: number;
}

export interface TrafficData {
  morning: number;
  afternoon: number;
  evening: number;
  night: number;
}

export interface NetworkEdge {
  from_id: string;
  to_id: string;
  distance: number;
  capacity: number;
  condition: number;
  traffic: TrafficData;
  is_existing: boolean;
  construction_cost: number | null;
}

export interface NetworkSummary {
  total_nodes: number;
  total_edges: number;
  existing_edges: number;
  candidate_edges: number;
  avg_congestion: number;
  network_coverage: number;
  active_assets: number;
}

export interface DbSummary {
  total_nodes: number;
  existing_roads: number;
  candidate_roads: number;
  metro_lines: number;
  bus_routes: number;
  total_metro_daily: number;
}

/* ─── Algorithm results ─── */

export interface ShortestPathResult {
  path: string[];
  path_names: string[];
  total_distance: number;
  total_cost: number;
  congestion_level: "LOW" | "MEDIUM" | "HIGH";
  avg_congestion_pct: number;
  estimated_time: number;
  reliability: number;
  report: Array<{
    edge: string;
    distance_km: number;
    congestion_pct: number;
    flow: number;
    capacity: number;
  }>;
}

export interface EmergencyResult {
  path: string[];
  path_names: string[];
  nearest_facility: string;
  facility_type: string;
  distance: number;
  estimated_time: number;
  nodes_explored: number;
}

export interface MSTEdge {
  from_id: string;
  to_id: string;
  distance: number;
  condition: number;
}

export interface MSTResult {
  edges: MSTEdge[];
  mandatory_edges: MSTEdge[];
  total_cost: number;
  total_distance: number;
  suggested_roads: Array<{
    road: string;
    distance_km: number;
    construction_cost: number;
    capacity: number;
    score: number;
  }>;
}

export interface BusAllocationResult {
  selected_routes: Array<{
    id: string;
    buses_assigned: number;
    daily_passengers: number;
    stops: string[];
  }>;
  total_buses: number;
  max_passengers: number;
  coverage: number;
}

export interface RoadMaintenanceResult {
  selected_roads: Array<{
    road: string;
    cost: number;
    value: number;
    improvement: number;
  }>;
  total_cost: number;
  roads_fixed: number;
  total_improvement: number;
}

export interface TrafficSignalsResult {
  green_times: Record<string, number>;
  overloaded_roads: string[];
  optimization_score: number;
}

export interface MemoizedPlannerResult {
  routes: Array<{
    target: string;
    target_name: string;
    cost: number;
    path: string[];
    path_names: string[];
  }>;
  cache_hits: number;
  cache_hit_rate: number;
  total_distance: number;
}

export interface RushHourResult {
  congested_roads: Array<{ road: string; congestion_pct: number }>;
  avg_congestion: number;
  recommendations: string[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  top_pairs: any[];
}

export interface RoadClosureResult {
  affected_routes: Array<{
    from: string;
    to: string;
    extra_cost: number | string;
    impact: string;
  }>;
  impact_score: number;
}

export interface NewRoadAnalysisResult {
  best_candidates: Array<{
    road: string;
    cost_effectiveness: number;
    congestion_reduction: number;
  }>;
}

export interface MlSamplePrediction {
  index: number;
  actual: number;
  predicted: number;
  absolute_error: number;
}

export interface MlWeightComparison {
  time_of_day: string;
  flow: number;
  capacity: number;
  distance: number;
  static_congestion: number;
  predicted_congestion: number;
  old_weight: number;
  ml_weight: number;
}

export interface MlCongestionModelResult {
  model_name: string;
  dataset_origin: string;
  sample_count: number;
  mse: number;
  average_absolute_error: number;
  features: string[];
  sample_predictions: MlSamplePrediction[];
  weight_comparison: MlWeightComparison;
}

export interface MlCongestionPredictionResult extends MlWeightComparison {
  model_name: string;
  dataset_origin: string;
}

export type VisualAlgorithm = "dijkstra" | "astar" | "greedy" | "bfs";

export interface RaceStep {
  current: string;
  visited: string[];
  frontier: string[];
  path: string[];
}

export interface RaceTrace {
  algorithm: VisualAlgorithm;
  label: string;
  steps: RaceStep[];
  final_path: string[];
  cost: number;
  path_length: number;
  visited_count: number;
  execution_time_ms: number;
  memory_units: number;
}

export interface RaceResult {
  source: string;
  target: string;
  source_name: string;
  target_name: string;
  time_of_day: string;
  left: RaceTrace;
  right: RaceTrace;
  summary: {
    winner: string;
    reason: string;
    explanation: string;
    step_count: number;
  };
}

export type AlgorithmType =
  | "shortest-path"
  | "emergency-routing"
  | "mst"
  | "bus-allocation"
  | "road-maintenance"
  | "traffic-signals"
  | "memoized-planner"
  | "rush-hour"
  | "road-closure"
  | "new-road-analysis";

export interface AlgorithmResult {
  type: AlgorithmType;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
  timestamp: number;
}

export interface SystemLog {
  id: number;
  message: string;
  type: "info" | "success" | "error" | "warning";
  timestamp: number;
}
