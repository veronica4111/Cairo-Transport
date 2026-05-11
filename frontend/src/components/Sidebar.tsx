import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Activity, Info, CheckCircle2, AlertTriangle, Zap } from "lucide-react";
import type { NetworkNode, AlgorithmType, AlgorithmResult, SystemLog } from "../types";

interface SidebarProps {
  nodes: NetworkNode[];
  onRunAlgorithm: (type: AlgorithmType, params: Record<string, unknown>) => void;
  isRunning: boolean;
  result: AlgorithmResult | null;
  logs: SystemLog[];
}

const ALGORITHMS: { value: AlgorithmType; label: string; category: string }[] = [
  { value: "shortest-path", label: "Shortest Path (Dijkstra)", category: "Pathfinding" },
  { value: "emergency-routing", label: "Emergency Routing (A*)", category: "Pathfinding" },
  { value: "mst", label: "MST Infrastructure Design", category: "Optimization" },
  { value: "bus-allocation", label: "Bus Allocation (DP)", category: "Optimization" },
  { value: "road-maintenance", label: "Road Maintenance (DP)", category: "Optimization" },
  { value: "traffic-signals", label: "Traffic Signal Optimizer", category: "Optimization" },
  { value: "memoized-planner", label: "Memoized Route Planner", category: "Pathfinding" },
  { value: "rush-hour", label: "Rush Hour Simulation", category: "Simulation" },
  { value: "road-closure", label: "Road Closure Impact", category: "Simulation" },
  { value: "new-road-analysis", label: "New Road Analysis", category: "Simulation" },
];

const TIME_OPTIONS = [
  { value: "morning", label: "Morning (06–12)" },
  { value: "afternoon", label: "Afternoon (12–17)" },
  { value: "evening", label: "Evening (17–21)" },
  { value: "night", label: "Night (21–06)" },
];

export default function Sidebar({ nodes, onRunAlgorithm, isRunning, result, logs }: SidebarProps) {
  const [selectedAlgo, setSelectedAlgo] = useState<AlgorithmType>("shortest-path");
  const [validationError, setValidationError] = useState<string>("");
  const [formData, setFormData] = useState<Record<string, string | number>>({
    source: "",
    target: "",
    time_of_day: "morning",
    incident_node: "",
    budget: 80,
    node_id: "",
    destinations: "",
    from_node: "",
    to_node: "",
  });

  // Auto-select first node when nodes load
  useEffect(() => {
    if (nodes.length > 0 && !formData.source) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setFormData((prev) => ({
        ...prev,
        source: nodes[0].id,
        target: nodes.length > 1 ? nodes[1].id : nodes[0].id,
        incident_node: nodes[0].id,
        node_id: nodes[0].id,
        from_node: nodes[0].id,
        to_node: nodes.length > 1 ? nodes[1].id : nodes[0].id,
      }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes]);

  const handleRun = () => {
    // Clear any previous validation errors
    setValidationError("");
    
    const params: Record<string, unknown> = {};
    switch (selectedAlgo) {
      case "shortest-path":
        params.source = String(formData.source);
        params.target = String(formData.target);
        params.time_of_day = String(formData.time_of_day);
        break;
      case "emergency-routing":
        params.incident_node = String(formData.incident_node);
        break;
      case "mst":
      case "new-road-analysis":
        break;
      case "bus-allocation":
        params.budget = Number(formData.budget) || 80;
        break;
      case "road-maintenance":
        params.budget = Number(formData.budget) || 350;
        break;
      case "traffic-signals":
        params.node_id = String(formData.node_id);
        params.time_of_day = String(formData.time_of_day);
        break;
      case "memoized-planner":
        params.source = String(formData.source);
        params.destinations = String(formData.destinations)
          .split(",")
          .map((s: string) => s.trim())
          .filter(Boolean);
        params.time_of_day = String(formData.time_of_day);
        break;
      case "rush-hour":
        params.time_of_day = String(formData.time_of_day);
        break;
      case "road-closure":
        // Validate that from and to nodes are different
        if (String(formData.from_node) === String(formData.to_node)) {
          const fromNode = nodes.find(n => n.id === String(formData.from_node));
          const errorMsg = `You cannot close a road from ${fromNode?.name || 'a node'} to itself. Please select two different nodes.`;
          setValidationError(errorMsg);
          console.error("Road Closure validation failed: same node selected");
          return; // Stop execution
        }
        params.from_node = String(formData.from_node);
        params.to_node = String(formData.to_node);
        break;
    }
    onRunAlgorithm(selectedAlgo, params);
  };

  const renderNodeDropdown = (key: string, label: string, value: string | number) => (
    <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="mb-3">
      <label className="block text-[10px] font-semibold tracking-wider mb-1.5 text-text-secondary">
        {label}
      </label>
      <select
        value={String(value)}
        onChange={(e) => {
          setFormData((prev) => ({ ...prev, [key]: e.target.value }));
          setValidationError(""); // Clear validation error when selection changes
        }}
        className="w-full px-3 py-2 rounded-md text-xs font-mono bg-bg-secondary border border-border-primary text-text-primary outline-none focus:border-teal/50 transition-colors"
      >
        {nodes.map((n) => (
          <option key={n.id} value={n.id}>
            {n.name} ({n.id})
          </option>
        ))}
      </select>
    </motion.div>
  );

  const renderTimeDropdown = () => (
    <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="mb-3">
      <label className="block text-[10px] font-semibold tracking-wider mb-1.5 text-text-secondary">
        TEMPORAL FILTER
      </label>
      <select
        value={String(formData.time_of_day)}
        onChange={(e) => setFormData((prev) => ({ ...prev, time_of_day: e.target.value }))}
        className="w-full px-3 py-2 rounded-md text-xs font-mono bg-bg-secondary border border-border-primary text-text-primary outline-none focus:border-teal/50 transition-colors"
      >
        {TIME_OPTIONS.map((t) => (
          <option key={t.value} value={t.value}>
            {t.label}
          </option>
        ))}
      </select>
    </motion.div>
  );

  const renderBudgetInput = (label: string, defaultVal: number) => (
    <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="mb-3">
      <label className="block text-[10px] font-semibold tracking-wider mb-1.5 text-text-secondary">
        {label}
      </label>
      <input
        type="number"
        value={Number(formData.budget)}
        onChange={(e) => setFormData((prev) => ({ ...prev, budget: e.target.value }))}
        placeholder={String(defaultVal)}
        className="w-full px-3 py-2 rounded-md text-xs font-mono bg-bg-secondary border border-border-primary text-text-primary outline-none focus:border-teal/50 transition-colors"
      />
    </motion.div>
  );

  const renderForm = () => {
    switch (selectedAlgo) {
      case "shortest-path":
        return (
          <>
            {renderNodeDropdown("source", "ORIGIN NODE", formData.source)}
            {renderNodeDropdown("target", "DESTINATION NODE", formData.target)}
            {renderTimeDropdown()}
          </>
        );
      case "emergency-routing":
        return renderNodeDropdown("incident_node", "INCIDENT LOCATION", formData.incident_node);
      case "mst":
      case "new-road-analysis":
        return (
          <p className="text-xs italic text-text-secondary">
            No parameters required. Click Run to execute.
          </p>
        );
      case "bus-allocation":
        return renderBudgetInput("TOTAL BUS BUDGET", 80);
      case "road-maintenance":
        return renderBudgetInput("MAINTENANCE BUDGET (M EGP)", 350);
      case "traffic-signals":
        return (
          <>
            {renderNodeDropdown("node_id", "INTERSECTION NODE", formData.node_id)}
            {renderTimeDropdown()}
          </>
        );
      case "memoized-planner":
        return (
          <>
            {renderNodeDropdown("source", "SOURCE NODE", formData.source)}
            <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="mb-3">
              <label className="block text-[10px] font-semibold tracking-wider mb-1.5 text-text-secondary">
                DESTINATIONS (comma-separated IDs)
              </label>
              <input
                type="text"
                value={String(formData.destinations)}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, destinations: e.target.value }))
                }
                placeholder="5, 9, 5, 10, 9"
                className="w-full px-3 py-2 rounded-md text-xs font-mono bg-bg-secondary border border-border-primary text-text-primary outline-none focus:border-teal/50 transition-colors"
              />
            </motion.div>
            {renderTimeDropdown()}
          </>
        );
      case "rush-hour":
        return renderTimeDropdown();
      case "road-closure":
        return (
          <>
            {renderNodeDropdown("from_node", "CLOSED ROAD FROM", formData.from_node)}
            {renderNodeDropdown("to_node", "CLOSED ROAD TO", formData.to_node)}
          </>
        );
      default:
        return null;
    }
  };

  const renderResult = () => {
    if (!result) return null;
    const { type, data } = result;
    
    // Debug logging
    console.log('Rendering result:', { type, data });

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="mt-4 p-4 rounded-xl bg-bg-secondary/60 border border-teal/30 shadow-[0_0_20px_var(--color-teal-glow)] backdrop-blur-md"
      >
        <div className="text-[10px] font-semibold tracking-wider mb-3 text-teal flex items-center gap-1.5">
          <Activity size={12} />
          RESULTS — {type.toUpperCase().replace(/-/g, " ")}
        </div>
        
        {/* Shortest Path */}
        {type === "shortest-path" && (
          <div className="space-y-3">
            {/* Complexity Badge */}
            {data.complexity && (
              <div className="text-[9px] font-mono text-text-muted bg-bg-tertiary px-2 py-1 rounded border border-border-primary">
                {data.complexity}
              </div>
            )}
            
            <div className="flex items-end gap-2">
              <span className="text-4xl font-bold text-teal">{data.estimated_time}</span>
              <span className="text-xs font-medium pb-1.5 text-text-secondary">MIN</span>
            </div>
            
            {/* Best Path Display */}
            {data.best_path && (
              <div className="bg-bg-tertiary/50 px-3 py-2 rounded-lg border border-border-primary">
                <div className="text-[9px] font-semibold tracking-wider text-text-secondary mb-1">
                  BEST PATH
                </div>
                <div className="text-[11px] font-mono text-teal">
                  {data.best_path}
                </div>
              </div>
            )}
            
            {/* Total Congestion Cost */}
            {data.total_congestion_cost && (
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-text-secondary">Total Congestion Cost:</span>
                <span className="font-mono font-bold text-orange">{data.total_congestion_cost}</span>
              </div>
            )}
            
            <div className="flex items-center gap-2">
              <span className="text-[10px] tracking-wider text-text-secondary">CONGESTION</span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  data.congestion_level === "LOW" ? "bg-teal/20 text-teal" :
                  data.congestion_level === "MEDIUM" ? "bg-orange/20 text-orange" :
                  "bg-red/20 text-red"
                }`}
              >
                {data.congestion_level}
              </span>
            </div>
            
            {/* Path Steps Table */}
            {data.path_steps && data.path_steps.length > 0 && (
              <div className="mt-3">
                <div className="text-[9px] font-semibold tracking-wider text-text-secondary mb-2">
                  ROUTE BREAKDOWN
                </div>
                <div className="space-y-1.5 max-h-[200px] overflow-y-auto pr-1">
                  {data.path_steps.map((step: any, idx: number) => {
                    const congestionPercent = parseFloat(step.congestion?.replace('%', '') || '0');
                    const congestionColor = 
                      congestionPercent < 70 ? 'text-teal' :
                      congestionPercent < 90 ? 'text-orange' : 'text-red';
                    
                    return (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="bg-bg-tertiary/30 px-2.5 py-2 rounded border border-border-primary hover:border-teal/30 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-mono font-semibold text-text-primary">
                            {step.step}
                          </span>
                          <span className={`text-[9px] font-bold ${congestionColor}`}>
                            {step.congestion}
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-1.5 text-[9px]">
                          <div>
                            <span className="text-text-secondary font-semibold">Dist:</span>
                            <span className="ml-1 text-teal font-mono font-bold">{step.distance_km} km</span>
                          </div>
                          <div>
                            <span className="text-text-secondary font-semibold">Flow:</span>
                            <span className="ml-1 text-blue font-mono font-bold">{step.flow}</span>
                          </div>
                          <div>
                            <span className="text-text-secondary font-semibold">Cap:</span>
                            <span className="ml-1 text-purple font-mono font-bold">{step.capacity}</span>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            )}
            
            <div>
              <span className="text-[10px] tracking-wider text-text-secondary">ROUTE RELIABILITY</span>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-border-primary">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${data.reliability}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full rounded-full"
                    style={{ background: `linear-gradient(90deg, var(--color-teal), ${data.reliability > 70 ? 'var(--color-teal)' : 'var(--color-orange)'})` }}
                  />
                </div>
                <span className="text-xs font-mono font-bold text-teal">{data.reliability}%</span>
              </div>
            </div>
            <div className="text-[10px] text-text-secondary">
              Distance: {data.total_distance} km · Cost: {data.total_cost}
            </div>
          </div>
        )}

        {/* Emergency Routing */}
        {type === "emergency-routing" && (
          <div className="space-y-2">
            <div className="flex items-end gap-2">
              <span className="text-4xl font-bold text-red">{data.estimated_time}</span>
              <span className="text-xs font-medium pb-1.5 text-text-secondary">MIN</span>
            </div>
            <div className="text-xs text-text-secondary">
              → {data.nearest_facility} ({data.facility_type})
            </div>
            <div className="text-xs text-text-secondary">
              Distance: {data.distance} km · Explored: {data.nodes_explored} nodes
            </div>
          </div>
        )}

        {/* MST */}
        {type === "mst" && (
          <div className="space-y-3">
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-green">{data.total_cost}</span>
              <span className="text-xs font-medium pb-1.5 text-text-secondary">M EGP</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="bg-bg-tertiary/50 px-2 py-1.5 rounded">
                <div className="text-text-secondary font-semibold">Total Distance</div>
                <div className="text-teal font-mono font-bold text-sm">{data.total_distance} km</div>
              </div>
              <div className="bg-bg-tertiary/50 px-2 py-1.5 rounded">
                <div className="text-text-secondary font-semibold">Edges</div>
                <div className="text-blue font-mono font-bold text-sm">{data.edges?.length || 0}</div>
              </div>
            </div>
            {data.suggested_roads && data.suggested_roads.length > 0 && (
              <div className="text-[10px]">
                <div className="text-text-secondary font-semibold mb-1">Suggested New Roads:</div>
                <div className="space-y-1.5">
                  {data.suggested_roads.map((road: any, idx: number) => {
                    // Extract node IDs from road string (e.g., "9 <-> 11")
                    const roadMatch = road.road.match(/(\w+)\s*<->\s*(\w+)/);
                    const fromId = roadMatch?.[1];
                    const toId = roadMatch?.[2];
                    const fromNode = nodes.find(n => n.id === fromId);
                    const toNode = nodes.find(n => n.id === toId);
                    const roadName = fromNode && toNode 
                      ? `${fromNode.name} ↔ ${toNode.name}`
                      : road.road;
                    
                    return (
                      <div key={idx} className="bg-bg-tertiary/30 px-2.5 py-2 rounded">
                        <div className="text-teal font-mono font-semibold mb-1 text-[11px]">{roadName}</div>
                        <div className="grid grid-cols-2 gap-2 text-[9px]">
                          <div>
                            <span className="text-text-secondary font-semibold">Distance:</span>
                            <span className="ml-1 text-blue font-bold">{road.distance_km} km</span>
                          </div>
                          <div>
                            <span className="text-text-secondary font-semibold">Cost:</span>
                            <span className="ml-1 text-red font-bold">{road.construction_cost} M</span>
                          </div>
                          <div>
                            <span className="text-text-secondary font-semibold">Capacity:</span>
                            <span className="ml-1 text-purple font-bold">{road.capacity}</span>
                          </div>
                          <div>
                            <span className="text-text-secondary font-semibold">Score:</span>
                            <span className="ml-1 text-green font-bold">{road.score?.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Bus Allocation */}
        {type === "bus-allocation" && (
          <div className="space-y-3">
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-blue">{data.total_buses}</span>
              <span className="text-xs font-medium pb-1.5 text-text-secondary">BUSES</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="bg-bg-tertiary/50 px-2 py-1.5 rounded">
                <div className="text-text-secondary font-semibold">Max Passengers</div>
                <div className="text-teal font-mono font-bold text-sm">{data.max_passengers?.toLocaleString()}</div>
              </div>
              <div className="bg-bg-tertiary/50 px-2 py-1.5 rounded">
                <div className="text-text-secondary font-semibold">Coverage</div>
                <div className="text-green font-mono font-bold text-sm">{data.coverage}%</div>
              </div>
            </div>
            {data.selected_routes && data.selected_routes.length > 0 && (
              <div className="text-[10px]">
                <div className="text-text-secondary font-semibold mb-1">Selected Routes:</div>
                <div className="space-y-1">
                  {data.selected_routes.slice(0, 3).map((route: any, idx: number) => (
                    <div key={idx} className="bg-bg-tertiary/30 px-2 py-1 rounded text-text-primary font-mono">
                      {route.id}: {route.buses_assigned} buses
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Road Maintenance */}
        {type === "road-maintenance" && (
          <div className="space-y-3">
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-orange">{data.roads_fixed}</span>
              <span className="text-xs font-medium pb-1.5 text-text-secondary">ROADS</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="bg-bg-tertiary/50 px-2 py-1.5 rounded">
                <div className="text-text-secondary font-semibold">Total Cost</div>
                <div className="text-red font-mono font-bold text-sm">{data.total_cost} M</div>
              </div>
              <div className="bg-bg-tertiary/50 px-2 py-1.5 rounded">
                <div className="text-text-secondary font-semibold">Improvement</div>
                <div className="text-green font-mono font-bold text-sm">+{data.total_improvement}</div>
              </div>
            </div>
            {data.selected_roads && data.selected_roads.length > 0 && (
              <div className="text-[10px]">
                <div className="text-text-secondary font-semibold mb-1">Fixed Roads:</div>
                <div className="space-y-1">
                  {data.selected_roads.map((road: any, idx: number) => {
                    // Extract node IDs from road string (e.g., "1-8" or "3-9")
                    const roadMatch = road.road.match(/(\w+)-(\w+)/);
                    const fromId = roadMatch?.[1];
                    const toId = roadMatch?.[2];
                    const fromNode = nodes.find(n => n.id === fromId);
                    const toNode = nodes.find(n => n.id === toId);
                    const roadName = fromNode && toNode 
                      ? `${fromNode.name} ↔ ${toNode.name}`
                      : road.road;
                    
                    return (
                      <div key={idx} className="bg-bg-tertiary/30 px-2 py-1 rounded flex justify-between text-text-primary">
                        <span className="font-mono text-[10px]">{roadName}</span>
                        <span className="text-green font-bold">+{road.improvement}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Traffic Signals */}
        {type === "traffic-signals" && (
          <div className="space-y-3">
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-orange">{data.optimization_score}</span>
              <span className="text-xs font-medium pb-1.5 text-text-secondary">SCORE</span>
            </div>
            {data.green_times && (
              <div className="text-[10px]">
                <div className="text-text-secondary font-semibold mb-1">Green Times (seconds):</div>
                <div className="space-y-1">
                  {Object.entries(data.green_times).map(([road, time]: [string, any], idx: number) => {
                    // Extract node IDs from road string (e.g., "2->3")
                    const roadMatch = road.match(/(\w+)->(\w+)/);
                    const fromId = roadMatch?.[1];
                    const toId = roadMatch?.[2];
                    const fromNode = nodes.find(n => n.id === fromId);
                    const toNode = nodes.find(n => n.id === toId);
                    const roadName = fromNode && toNode 
                      ? `${fromNode.name} → ${toNode.name}`
                      : road;
                    
                    return (
                      <div key={idx} className="bg-bg-tertiary/30 px-2 py-1 rounded flex justify-between">
                        <span className="text-text-primary font-mono text-[10px]">{roadName}</span>
                        <span className="text-teal font-bold">{time}s</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Memoized Planner */}
        {type === "memoized-planner" && (
          <div className="space-y-3">
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-purple">{data.cache_hit_rate}</span>
              <span className="text-xs font-medium pb-1.5 text-text-secondary">% CACHED</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="bg-bg-tertiary/50 px-2 py-1.5 rounded">
                <div className="text-text-secondary font-semibold">Total Distance</div>
                <div className="text-teal font-mono font-bold text-sm">{data.total_distance} km</div>
              </div>
              <div className="bg-bg-tertiary/50 px-2 py-1.5 rounded">
                <div className="text-text-secondary font-semibold">Cache Hits</div>
                <div className="text-green font-mono font-bold text-sm">{data.cache_hits}</div>
              </div>
            </div>
            {data.routes && data.routes.length > 0 && (
              <div className="text-[10px]">
                <div className="text-text-secondary font-semibold mb-1">Routes:</div>
                <div className="space-y-1 max-h-[150px] overflow-y-auto">
                  {data.routes.map((route: any, idx: number) => (
                    <div key={idx} className="bg-bg-tertiary/30 px-2 py-1 rounded">
                      <div className="text-text-primary font-mono">{route.target_name}</div>
                      <div className="text-teal text-[9px]">{route.cost} km</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Rush Hour */}
        {type === "rush-hour" && (
          <div className="space-y-3">
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-red">{data.avg_congestion}</span>
              <span className="text-xs font-medium pb-1.5 text-text-secondary">% AVG</span>
            </div>
            {data.congested_roads && data.congested_roads.length > 0 && (
              <div className="text-[10px]">
                <div className="text-text-secondary font-semibold mb-1">Congested Roads:</div>
                <div className="space-y-1 max-h-[150px] overflow-y-auto">
                  {data.congested_roads.map((item: any, idx: number) => {
                    // Extract node IDs from road string (e.g., "1-3")
                    const roadMatch = item.road.match(/(\w+)-(\w+)/);
                    const fromId = roadMatch?.[1];
                    const toId = roadMatch?.[2];
                    const fromNode = nodes.find(n => n.id === fromId);
                    const toNode = nodes.find(n => n.id === toId);
                    const roadName = fromNode && toNode 
                      ? `${fromNode.name} → ${toNode.name}`
                      : item.road;
                    
                    return (
                      <div key={idx} className="bg-bg-tertiary/30 px-2 py-1 rounded flex justify-between">
                        <span className="text-text-primary font-mono text-[10px]">{roadName}</span>
                        <span className="text-red font-bold">{item.congestion_pct}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Road Closure */}
        {type === "road-closure" && (
          <div className="space-y-3">
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-red">{data.impact_score}</span>
              <span className="text-xs font-medium pb-1.5 text-text-secondary">IMPACT</span>
            </div>
            {data.affected_routes && data.affected_routes.length > 0 ? (
              <div className="text-[10px]">
                <div className="text-text-secondary font-semibold mb-1">Affected Routes:</div>
                <div className="space-y-1 max-h-[150px] overflow-y-auto">
                  {data.affected_routes.map((route: any, idx: number) => {
                    const fromNode = nodes.find(n => n.id === route.from);
                    const toNode = nodes.find(n => n.id === route.to);
                    const fromName = fromNode?.name || route.from;
                    const toName = toNode?.name || route.to;
                    
                    return (
                      <div key={idx} className="bg-bg-tertiary/30 px-2 py-1 rounded">
                        <div className="text-text-primary font-mono text-[10px]">{fromName} → {toName}</div>
                        <div className="text-orange text-[9px]">
                          {route.extra_cost === "No alternate route" 
                            ? "No alternate route available" 
                            : `+${route.extra_cost} km · ${route.impact} impact`}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="text-[10px] text-text-secondary italic">
                No high-demand routes use this road. Impact is minimal.
              </div>
            )}
          </div>
        )}

        {/* New Road Analysis */}
        {type === "new-road-analysis" && (
          <div className="space-y-3">
            {data.best_candidates && data.best_candidates.length > 0 && (
              <div className="text-[10px]">
                <div className="text-text-secondary font-semibold mb-2">Best Candidates:</div>
                <div className="space-y-1.5 max-h-[250px] overflow-y-auto pr-1">
                  {data.best_candidates.map((candidate: any, idx: number) => {
                    // Extract node IDs from road string (e.g., "9 <-> 11")
                    const roadMatch = candidate.road.match(/(\w+)\s*<->\s*(\w+)/);
                    const fromId = roadMatch?.[1];
                    const toId = roadMatch?.[2];
                    const fromNode = nodes.find(n => n.id === fromId);
                    const toNode = nodes.find(n => n.id === toId);
                    const roadName = fromNode && toNode 
                      ? `${fromNode.name} ↔ ${toNode.name}`
                      : candidate.road;
                    
                    return (
                      <div key={idx} className="bg-bg-tertiary/30 px-2.5 py-2 rounded">
                        <div className="text-text-primary font-mono font-semibold mb-1 text-[11px]">{roadName}</div>
                        <div className="grid grid-cols-2 gap-2 text-[9px]">
                          <div>
                            <span className="text-text-secondary font-semibold">Effectiveness:</span>
                            <span className="ml-1 text-teal font-bold">{candidate.cost_effectiveness}</span>
                          </div>
                          <div>
                            <span className="text-text-secondary font-semibold">Reduction:</span>
                            <span className="ml-1 text-green font-bold">{candidate.congestion_reduction}%</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Fallback for unknown types */}
        {!["shortest-path", "emergency-routing", "mst", "bus-allocation", "road-maintenance", 
            "traffic-signals", "memoized-planner", "rush-hour", "road-closure", "new-road-analysis"].includes(type) && (
          <div className="space-y-2">
             <pre className="text-[10px] font-mono overflow-auto max-h-40 text-text-secondary">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
      </motion.div>
    );
  };

  return (
    <motion.aside
      initial={{ x: -280 }}
      animate={{ x: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="flex flex-col h-full overflow-hidden w-[280px] min-w-[280px] bg-bg-primary/80 backdrop-blur-xl border-r border-border-primary z-40 relative"
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-border-primary flex items-center gap-3">
        <div className="p-1.5 bg-teal/20 text-teal rounded-lg shadow-[0_0_10px_var(--color-teal-glow)]">
          <Zap size={18} />
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-wide text-teal">
            Cairo Transport AI
          </h1>
          <p className="text-[10px] mt-0.5 text-text-muted">
            Omniscient Control v4.0
          </p>
        </div>
      </div>

      {/* Algorithm selector */}
      <div className="px-5 py-4 flex-1 overflow-y-auto">
        <label className="block text-[10px] font-semibold tracking-[0.15em] mb-2 text-text-secondary">
          SELECTED ALGORITHM
        </label>
        <select
          value={selectedAlgo}
          onChange={(e) => {
            setSelectedAlgo(e.target.value as AlgorithmType);
            setValidationError(""); // Clear validation error when algorithm changes
          }}
          className="w-full px-3 py-2.5 rounded-md text-xs font-medium mb-5 bg-bg-secondary border border-border-primary text-text-primary outline-none focus:border-teal/50 transition-colors shadow-sm"
        >
          {ALGORITHMS.map((a) => (
            <option key={a.value} value={a.value}>
              {a.label}
            </option>
          ))}
        </select>

        {/* Dynamic form */}
        <div className="mb-5">{renderForm()}</div>

        {/* Validation Error Message */}
        <AnimatePresence>
          {validationError && (
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="mb-3 p-3 rounded-lg bg-red/20 border border-red/50 flex items-start gap-2"
            >
              <AlertTriangle size={16} className="text-red flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="text-[10px] font-bold text-red mb-1">INVALID SELECTION</div>
                <div className="text-[10px] text-text-primary leading-relaxed">{validationError}</div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Run button */}
        <motion.button
          whileHover={{ scale: isRunning ? 1 : 1.02 }}
          whileTap={{ scale: isRunning ? 1 : 0.98 }}
          onClick={handleRun}
          disabled={isRunning}
          className={`w-full py-3 rounded-lg font-bold text-xs tracking-wider transition-all duration-300 flex items-center justify-center gap-2 ${
            isRunning 
              ? 'bg-teal/40 text-bg-primary cursor-not-allowed shadow-none'
              : 'bg-teal text-bg-primary cursor-pointer hover:shadow-[0_0_20px_var(--color-teal-glow)]'
          }`}
        >
          {isRunning ? (
            <>
              <span className="spinner border-t-bg-primary" />
              RUNNING...
            </>
          ) : (
            <>
              <Play size={14} fill="currentColor" /> 
              Run Algorithm
            </>
          )}
        </motion.button>

        {/* Results card */}
        <AnimatePresence>
          {result && renderResult()}
        </AnimatePresence>
      </div>

      {/* System Logs */}
      <div className="border-t border-border-primary bg-bg-secondary/30 px-5 py-3 h-[180px] flex flex-col">
        <div className="text-[10px] font-semibold tracking-wider mb-2 text-text-muted flex items-center gap-1.5">
          <Info size={12} />
          SYSTEM LOGS
        </div>
        <div className="overflow-y-auto flex-1 space-y-1.5 pr-1">
          {logs.slice(-8).map((log) => (
            <motion.div
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              key={log.id} 
              className={`text-[10px] font-mono leading-relaxed flex items-start gap-1.5 ${
                log.type === "error" ? "text-red" :
                log.type === "success" ? "text-teal" :
                log.type === "warning" ? "text-orange" :
                "text-text-secondary"
              }`}
            >
              <span className="mt-0.5">
                {log.type === "error" ? <AlertTriangle size={10} /> : 
                 log.type === "success" ? <CheckCircle2 size={10} /> : 
                 log.type === "warning" ? <AlertTriangle size={10} /> : 
                 "›"}
              </span>
              <span>{log.message}</span>
            </motion.div>
          ))}
          {logs.length === 0 && (
            <div className="text-[10px] italic text-text-muted text-center mt-4">
              System ready...
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
