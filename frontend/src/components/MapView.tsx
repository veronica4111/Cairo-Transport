import { useEffect, useMemo, useRef, useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Polyline,
  Popup,
  useMap,
  Tooltip,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { NetworkNode, NetworkEdge, AlgorithmResult } from "../types";

/* ─── Constants ─── */
const CAIRO_CENTER: [number, number] = [30.02, 31.25];
const DEFAULT_ZOOM = 11;
const LIGHT_TILE_URL = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
const DARK_TILE_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";

const TYPE_COLORS: Record<string, string> = {
  Residential: "#2563eb",
  Business: "#7c3aed",
  Mixed: "#f59e0b",
  Industrial: "#dc2626",
  Government: "#059669",
  Medical: "#e11d48",
  Airport: "#ea580c",
  "Transport Hub": "#64748b",
  Education: "#0891b2",
  Tourism: "#06b6d4",
  Sports: "#8b5cf6",
  Commercial: "#6366f1",
};

const FACILITY_TYPES = [
  "Medical",
  "Airport",
  "Transport Hub",
  "Education",
  "Tourism",
  "Sports",
  "Commercial",
  "Business",
];

const NODE_LABELS: Record<string, string> = {
  F9: "QASR_EL_AINI",
  F10: "MAADI_MIL",
  F1: "CAI_INTL",
  F2: "RAMSES_STN",
};

function congestionColor(ratio: number): string {
  if (ratio < 0.7) return "#10b981";
  if (ratio < 0.9) return "#f59e0b";
  return "#ef4444";
}

function getNodeSize(node: NetworkNode): number {
  if (FACILITY_TYPES.includes(node.node_type)) return 5;
  if (node.population >= 500000) return 10;
  if (node.population >= 300000) return 8;
  if (node.population >= 150000) return 7;
  return 6;
}

/* ─── Animated path overlay ─── */
function AnimatedPath({
  positions,
  color = "#3b82f6",
}: {
  positions: [number, number][];
  color?: string;
}) {
  const map = useMap();
  const polyRef = useRef<L.Polyline | null>(null);

  useEffect(() => {
    if (positions.length < 2) return;

    const poly = L.polyline(positions, {
      color,
      weight: 5,
      opacity: 1,
      dashArray: "12 8",
      className: "animated-path",
    }).addTo(map);

    polyRef.current = poly;

    // Glow effect
    const glow = L.polyline(positions, {
      color,
      weight: 12,
      opacity: 0.3,
    }).addTo(map);

    return () => {
      map.removeLayer(poly);
      map.removeLayer(glow);
    };
  }, [positions, color, map]);

  return null;
}

/* ─── Pulsing marker for highlighted nodes ─── */
function PulsingMarker({
  position,
  color,
  size = 12,
}: {
  position: [number, number];
  color: string;
  size?: number;
}) {
  const map = useMap();

  useEffect(() => {
    const icon = L.divIcon({
      className: "",
      html: `
        <div style="
          width: ${size * 2}px; height: ${size * 2}px;
          border-radius: 50%;
          border: 2px solid ${color};
          animation: pulse-ring 2s ease-in-out infinite;
          position: relative;
        ">
          <div style="
            position: absolute; top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: ${size}px; height: ${size}px;
            border-radius: 50%;
            background: ${color};
            opacity: 0.6;
          "></div>
        </div>
      `,
      iconSize: [size * 2, size * 2],
      iconAnchor: [size, size],
    });

    const marker = L.marker(position, { icon, interactive: false }).addTo(map);
    return () => {
      map.removeLayer(marker);
    };
  }, [position, color, size, map]);

  return null;
}

/* ─── Direction arrow at midpoint of a road ─── */
function DirectionArrow({
  from,
  to,
  color,
}: {
  from: [number, number];
  to: [number, number];
  color: string;
}) {
  const map = useMap();

  useEffect(() => {
    const midLat = (from[0] + to[0]) / 2;
    const midLon = (from[1] + to[1]) / 2;
    const angle = Math.atan2(to[1] - from[1], to[0] - from[0]) * (180 / Math.PI);

    const icon = L.divIcon({
      className: "",
      html: `<div style="
        width: 0; height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-bottom: 8px solid ${color};
        transform: rotate(${90 - angle}deg);
        filter: drop-shadow(0 0 2px ${color});
        opacity: 0.9;
      "></div>`,
      iconSize: [10, 8],
      iconAnchor: [5, 4],
    });

    const marker = L.marker([midLat, midLon], { icon, interactive: false }).addTo(map);
    return () => { map.removeLayer(marker); };
  }, [from, to, color, map]);

  return null;
}

/* ─── Layers panel with checkboxes ─── */
interface LayerVisibility {
  existingRoads: boolean;
  candidateRoads: boolean;
  directionArrows: boolean;
  nodeLabels: boolean;
}

function LayersPanel({
  layers,
  onChange,
  selectedNode,
  isDarkMode,
}: {
  layers: LayerVisibility;
  onChange: (key: keyof LayerVisibility) => void;
  selectedNode: string | null;
  isDarkMode: boolean;
}) {
  const [open, setOpen] = useState(false);

  const items: { key: keyof LayerVisibility; label: string; color: string }[] = [
    { key: "existingRoads", label: "Existing Roads", color: "#10b981" },
    { key: "candidateRoads", label: "Candidate Roads", color: "#94a3b8" },
    { key: "directionArrows", label: "Direction Arrows", color: "#f59e0b" },
    { key: "nodeLabels", label: "Node Labels", color: "#3b82f6" },
  ];

  return (
    <div
      className="absolute top-3 right-3 z-[1000] flex flex-col items-end gap-2"
    >
      {/* NETWORK LIVE badge */}
      <div
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-mono font-bold tracking-wider shadow-lg"
        style={{
          background: isDarkMode ? "rgba(13, 17, 23, 0.95)" : "rgba(255, 255, 255, 0.95)",
          border: isDarkMode ? "1px solid #00d4aa60" : "1px solid #10b98160",
          color: isDarkMode ? "#00d4aa" : "#059669",
        }}
      >
        <span className="w-2 h-2 rounded-full animate-pulse"
          style={{ background: isDarkMode ? "#00d4aa" : "#10b981", boxShadow: isDarkMode ? "0 0 8px #00d4aa" : "0 0 8px #10b981" }} />
        NETWORK LIVE
        <span className="w-2 h-2 rounded-full animate-pulse"
          style={{ background: isDarkMode ? "#00d4aa" : "#10b981", boxShadow: isDarkMode ? "0 0 8px #00d4aa" : "0 0 8px #10b981" }} />
      </div>

      {/* Layers toggle button */}
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[10px] font-mono font-bold tracking-wider shadow-lg transition-all"
        style={{
          background: isDarkMode 
            ? (open ? "#161b22" : "rgba(13, 17, 23, 0.95)")
            : (open ? "rgba(255, 255, 255, 0.98)" : "rgba(255, 255, 255, 0.95)"),
          border: isDarkMode
            ? `1px solid ${open ? "#00d4aa40" : "#30363d"}`
            : `1px solid ${open ? "#3b82f6" : "#cbd5e1"}`,
          color: isDarkMode
            ? (open ? "#00d4aa" : "#8b949e")
            : (open ? "#3b82f6" : "#64748b"),
          cursor: "pointer",
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2">
          <polygon points="12 2 2 7 12 12 22 7" />
          <polyline points="2 17 12 22 22 17" />
          <polyline points="2 12 12 17 22 12" />
        </svg>
        LAYERS
      </button>

      {/* Layers panel */}
      {open && (
        <div
          className="rounded-lg p-3 space-y-2 shadow-xl"
          style={{
            background: isDarkMode ? "#161b22" : "rgba(255, 255, 255, 0.98)",
            border: isDarkMode ? "1px solid #30363d" : "1px solid #e2e8f0",
            minWidth: 180,
          }}
        >
          {items.map((item) => (
            <label
              key={item.key}
              className={`flex items-center gap-2 cursor-pointer text-[11px] font-mono px-2 py-1 rounded transition-colors ${
                isDarkMode ? "hover:bg-bg-tertiary" : "hover:bg-slate-50"
              }`}
              style={{ color: isDarkMode ? "#e6edf3" : "#334155" }}
            >
              <input
                type="checkbox"
                checked={layers[item.key]}
                onChange={() => onChange(item.key)}
                className="hidden"
              />
              <div
                className="w-4 h-4 rounded border flex items-center justify-center transition-all"
                style={{
                  borderColor: layers[item.key] ? item.color : (isDarkMode ? "#484f58" : "#cbd5e1"),
                  background: layers[item.key] ? `${item.color}30` : "transparent",
                }}
              >
                {layers[item.key] && (
                  <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-6" stroke={item.color} strokeWidth="2" />
                  </svg>
                )}
              </div>
              <span
                className="w-2 h-2 rounded-full shadow-sm"
                style={{ background: item.color }}
              />
              {item.label}
            </label>
          ))}
        </div>
      )}

      {/* Selected node label */}
      {selectedNode && (
        <div
          className="px-3 py-1.5 rounded-lg text-[10px] font-mono font-semibold shadow-lg"
          style={{
            background: isDarkMode ? "rgba(13, 17, 23, 0.95)" : "rgba(255, 255, 255, 0.95)",
            border: isDarkMode ? "1px solid #30363d" : "1px solid #cbd5e1",
            color: isDarkMode ? "#8b949e" : "#475569",
          }}
        >
          {selectedNode}
        </div>
      )}
    </div>
  );
}

/* ─── FitBounds — auto-zoom to show all nodes ─── */
function FitBoundsOnLoad({ nodes }: { nodes: NetworkNode[] }) {
  const map = useMap();
  useEffect(() => {
    if (nodes.length === 0) return;
    const lats = nodes.map((n) => n.lat);
    const lons = nodes.map((n) => n.lon);
    const bounds: [[number, number], [number, number]] = [
      [Math.min(...lats) - 0.05, Math.min(...lons) - 0.05],
      [Math.max(...lats) + 0.05, Math.max(...lons) + 0.05],
    ];
    map.fitBounds(bounds, { padding: [30, 30], maxZoom: 13 });
  }, [nodes, map]);
  return null;
}

/* ─── RecenterButton ─── */
function RecenterButton({ nodes }: { nodes: NetworkNode[] }) {
  const map = useMap();
  const handleClick = () => {
    if (nodes.length > 0) {
      const lats = nodes.map((n) => n.lat);
      const lons = nodes.map((n) => n.lon);
      const bounds: [[number, number], [number, number]] = [
        [Math.min(...lats) - 0.05, Math.min(...lons) - 0.05],
        [Math.max(...lats) + 0.05, Math.max(...lons) + 0.05],
      ];
      map.fitBounds(bounds, { padding: [30, 30], maxZoom: 13 });
    } else {
      map.setView(CAIRO_CENTER, DEFAULT_ZOOM);
    }
  };
  return (
    <div className="absolute top-3 left-[60px] z-[1000]">
      <button
        onClick={handleClick}
        className="w-8 h-8 rounded-lg flex items-center justify-center text-sm shadow-lg hover:shadow-xl transition-all"
        style={{
          background: "rgba(255, 255, 255, 0.95)",
          border: "1px solid #cbd5e1",
          color: "#3b82f6",
          cursor: "pointer",
        }}
        title="Recenter to Cairo"
      >
        ⊕
      </button>
    </div>
  );
}

/* ─── Main MapView ─── */
interface MapViewProps {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  algorithmResult: AlgorithmResult | null;
}

export default function MapView({ nodes, edges, algorithmResult }: MapViewProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [layers, setLayers] = useState<LayerVisibility>({
    existingRoads: true,
    candidateRoads: true,
    directionArrows: true,
    nodeLabels: true,
  });

  // Listen for dark mode toggle
  useEffect(() => {
    const handleDarkModeToggle = (event: CustomEvent) => {
      setIsDarkMode(event.detail.isDark);
    };
    
    window.addEventListener('darkModeToggle', handleDarkModeToggle as EventListener);
    return () => {
      window.removeEventListener('darkModeToggle', handleDarkModeToggle as EventListener);
    };
  }, []);

  const toggleLayer = (key: keyof LayerVisibility) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Build a node lookup
  const nodeMap = useMemo(() => {
    const m: Record<string, NetworkNode> = {};
    nodes.forEach((n) => (m[n.id] = n));
    return m;
  }, [nodes]);

  // Parse algorithm result for path visualization
  const resultPath = useMemo<[number, number][]>(() => {
    if (!algorithmResult) return [];
    const { type, data } = algorithmResult;

    let pathIds: string[] = [];
    if (type === "shortest-path" || type === "emergency-routing" || type === "memoized-planner") {
      if (type === "memoized-planner") {
        // Use first route
        pathIds = data.routes?.[0]?.path || [];
      } else {
        pathIds = data.path || [];
      }
    }

    return pathIds
      .map((id: string) => nodeMap[id])
      .filter(Boolean)
      .map((n: NetworkNode) => [n.lat, n.lon] as [number, number]);
  }, [algorithmResult, nodeMap]);

  // MST edges
  const mstEdges = useMemo<Array<{ from: [number, number]; to: [number, number]; isMandatory: boolean }>>(() => {
    if (!algorithmResult || algorithmResult.type !== "mst") return [];
    const { data } = algorithmResult;

    const allMstEdges = (data.edges || []).map((e: { from_id: string; to_id: string }) => ({
      from: [nodeMap[e.from_id]?.lat || 0, nodeMap[e.from_id]?.lon || 0] as [number, number],
      to: [nodeMap[e.to_id]?.lat || 0, nodeMap[e.to_id]?.lon || 0] as [number, number],
      isMandatory: (data.mandatory_edges || []).some(
        (m: { from_id: string; to_id: string }) => m.from_id === e.from_id && m.to_id === e.to_id
      ),
    }));
    return allMstEdges;
  }, [algorithmResult, nodeMap]);

  // Highlighted nodes from algorithm
  const highlightedNodes = useMemo<string[]>(() => {
    if (!algorithmResult) return [];
    const { type, data } = algorithmResult;
    if (type === "shortest-path" || type === "emergency-routing") {
      return data.path || [];
    }
    if (type === "memoized-planner") {
      return data.routes?.[0]?.path || [];
    }
    return [];
  }, [algorithmResult]);

  // Compute node statuses
  const nodeStatuses = useMemo(() => {
    const statuses: Record<string, string> = {};
    if (!algorithmResult) return statuses;
    const { type, data } = algorithmResult;

    if (type === "shortest-path" && data.path) {
      data.path.forEach((id: string, i: number) => {
        if (i === 0) statuses[id] = "ORIGIN";
        else if (i === data.path.length - 1) statuses[id] = "DESTINATION";
        else statuses[id] = "OPTIMAL";
      });
    }
    if (type === "emergency-routing" && data.path) {
      data.path.forEach((id: string, i: number) => {
        if (i === 0) statuses[id] = "INCIDENT";
        else if (i === data.path.length - 1) statuses[id] = "HOSPITAL";
        else statuses[id] = "ROUTE";
      });
    }
    if (type === "rush-hour") {
      data.congested_roads?.forEach((r: { road: string }) => {
        const parts = r.road.split("-");
        parts.forEach((id: string) => {
          statuses[id] = "CRITICAL FLOW";
        });
      });
    }
    return statuses;
  }, [algorithmResult]);

  const pathColor = algorithmResult?.type === "emergency-routing" ? "#ef4444" : "#3b82f6";

  return (
    <div className="relative flex-1 h-full">
      <LayersPanel layers={layers} onChange={toggleLayer} selectedNode={selectedNode} isDarkMode={isDarkMode} />

      <MapContainer
        center={CAIRO_CENTER}
        zoom={DEFAULT_ZOOM}
        style={{ height: "100%", width: "100%" }}
        zoomControl={true}
        key={isDarkMode ? 'dark' : 'light'}
      >
        <TileLayer url={isDarkMode ? DARK_TILE_URL : LIGHT_TILE_URL} attribution="" />
        <FitBoundsOnLoad nodes={nodes} />
        <RecenterButton nodes={nodes} />

        {/* ─── Candidate roads (dashed gray) ─── */}
        {layers.candidateRoads && edges
          .filter((e) => !e.is_existing)
          .map((edge) => {
            const from = nodeMap[edge.from_id];
            const to = nodeMap[edge.to_id];
            if (!from || !to) return null;
            return (
              <Polyline
                key={`cand-${edge.from_id}-${edge.to_id}`}
                positions={[
                  [from.lat, from.lon],
                  [to.lat, to.lon],
                ]}
                pathOptions={{
                  color: "#94a3b8",
                  weight: 2.5,
                  dashArray: "8 6",
                  opacity: 0.7,
                }}
              >
                <Popup>
                  <div className="text-xs font-mono">
                    <div className="font-bold text-[#f59e0b]">CANDIDATE ROAD</div>
                    <div>
                      {from.name} ↔ {to.name}
                    </div>
                    <div>Distance: {edge.distance} km</div>
                    <div>Capacity: {edge.capacity}</div>
                    <div>Cost: {edge.construction_cost} M EGP</div>
                  </div>
                </Popup>
              </Polyline>
            );
          })}

        {/* ─── Existing roads (colored by congestion) ─── */}
        {layers.existingRoads && edges
          .filter((e) => e.is_existing)
          .map((edge) => {
            const from = nodeMap[edge.from_id];
            const to = nodeMap[edge.to_id];
            if (!from || !to) return null;
            const morningFlow = edge.traffic?.morning || 0;
            const ratio = edge.capacity > 0 ? morningFlow / edge.capacity : 0;
            const color = congestionColor(ratio);
            const fromPos: [number, number] = [from.lat, from.lon];
            const toPos: [number, number] = [to.lat, to.lon];

            return (
              <span key={`road-${edge.from_id}-${edge.to_id}`}>
                <Polyline
                  positions={[fromPos, toPos]}
                  pathOptions={{
                    color,
                    weight: 4,
                    opacity: 1,
                  }}
                >
                  <Popup>
                    <div className="text-xs font-mono">
                      <div className="font-bold" style={{ color }}>
                        {from.name} → {to.name}
                      </div>
                      <div>Distance: {edge.distance} km</div>
                      <div>Capacity: {edge.capacity}</div>
                      <div>
                        Morning: {edge.traffic?.morning} | Evening:{" "}
                        {edge.traffic?.evening}
                      </div>
                      <div>Condition: {edge.condition}/10</div>
                      <div>Congestion: {(ratio * 100).toFixed(1)}%</div>
                    </div>
                  </Popup>
                </Polyline>
                {layers.directionArrows && (
                  <DirectionArrow from={fromPos} to={toPos} color={color} />
                )}
              </span>
            );
          })}

        {/* ─── MST edges overlay ─── */}
        {mstEdges.map((e, i) => (
          <Polyline
            key={`mst-${i}`}
            positions={[e.from, e.to]}
            pathOptions={{
              color: e.isMandatory ? "#ef4444" : "#10b981",
              weight: e.isMandatory ? 5 : 4,
              opacity: 1,
              dashArray: e.isMandatory ? undefined : "10 6",
            }}
          />
        ))}

        {/* ─── Animated result path ─── */}
        {resultPath.length > 1 && (
          <AnimatedPath positions={resultPath} color={pathColor} />
        )}

        {/* ─── Pulsing markers for highlighted nodes ─── */}
        {highlightedNodes.map((id) => {
          const node = nodeMap[id];
          if (!node) return null;
          return (
            <PulsingMarker
              key={`pulse-${id}`}
              position={[node.lat, node.lon]}
              color={pathColor}
              size={14}
            />
          );
        })}

        {/* ─── Node markers ─── */}
        {nodes.map((node) => {
          const isFacility = FACILITY_TYPES.includes(node.node_type);
          const color = TYPE_COLORS[node.node_type] || "#8b949e";
          const size = getNodeSize(node);
          const isIndustrial = node.node_type === "Industrial";
          const label =
            NODE_LABELS[node.id] || node.name.toUpperCase().replace(/ /g, "_");
          const status = nodeStatuses[node.id];
          const displayLabel = status ? `${label} [${status}]` : label;

          return (
            <CircleMarker
              key={node.id}
              center={[node.lat, node.lon]}
              radius={size}
              pathOptions={{
                fillColor: color,
                fillOpacity: 0.9,
                color: isIndustrial ? "#ef4444" : color,
                weight: isFacility ? 2.5 : 2,
                opacity: 1,
              }}
              eventHandlers={{
                click: () => setSelectedNode(displayLabel),
              }}
            >
              {layers.nodeLabels && (
                <Tooltip
                  direction="top"
                  offset={[0, -8]}
                  permanent={false}
                  className="!bg-transparent !border-0 !shadow-none"
                >
                  <span
                    className="text-[9px] font-mono font-bold tracking-wider px-1.5 py-0.5 rounded"
                    style={{
                      color: status ? "#1e40af" : "#475569",
                      textShadow: "0 0 3px rgba(255,255,255,0.9), 0 1px 2px rgba(0,0,0,0.2)",
                      background: "rgba(255, 255, 255, 0.85)",
                    }}
                  >
                    {displayLabel}
                  </span>
                </Tooltip>
              )}
              <Popup>
                <div className="text-xs font-mono space-y-1">
                  <div className="font-bold text-sm" style={{ color }}>
                    {node.name}
                  </div>
                  <div>Type: {node.node_type}</div>
                  {node.population > 0 && (
                    <div>Population: {node.population.toLocaleString()}</div>
                  )}
                  <div>Connected Roads: {node.connected_roads}</div>
                  <div className="text-[10px] opacity-60">
                    [{node.lat.toFixed(4)}, {node.lon.toFixed(4)}]
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* ─── Animated path CSS ─── */}
      <style>{`
        .animated-path {
          animation: dash-anim 1.5s linear forwards;
          stroke-dasharray: 1000;
          stroke-dashoffset: 1000;
        }
        @keyframes dash-anim {
          to { stroke-dashoffset: 0; }
        }
      `}</style>
    </div>
  );
}
