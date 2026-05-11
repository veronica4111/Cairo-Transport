import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Info } from "lucide-react";

export interface ToastMessage {
  id: number;
  message: string;
  type: "error" | "success" | "info";
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  onRemove: (id: number) => void;
}

export default function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed top-16 right-6 z-[9999] flex flex-col gap-3" style={{ maxWidth: 360 }}>
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onRemove }: { toast: ToastMessage; onRemove: (id: number) => void }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => onRemove(toast.id), 300);
    }, 5000);
    return () => clearTimeout(timer);
  }, [toast.id, onRemove]);

  const colors = {
    error: { bg: "bg-red/10", border: "border-red/40", text: "text-red", shadow: "shadow-[0_0_15px_var(--color-red)]", icon: <XCircle size={16} /> },
    success: { bg: "bg-teal/10", border: "border-teal/40", text: "text-teal", shadow: "shadow-[0_0_15px_var(--color-teal-glow)]", icon: <CheckCircle2 size={16} /> },
    info: { bg: "bg-blue/10", border: "border-blue/40", text: "text-blue", shadow: "shadow-[0_0_15px_var(--color-blue)]", icon: <Info size={16} /> },
  };

  const c = colors[toast.type];

  return (
    <div
      className={`px-4 py-3.5 rounded-lg text-xs font-mono transition-all duration-300 flex items-start gap-3 backdrop-blur-xl border ${c.bg} ${c.border} ${c.text} ${c.shadow}`}
      style={{
        transform: visible ? "translateX(0) scale(1)" : "translateX(120%) scale(0.95)",
        opacity: visible ? 1 : 0,
      }}
    >
      <span className="mt-0.5">{c.icon}</span>
      <span className="flex-1 leading-relaxed">{toast.message}</span>
      <button
        onClick={() => onRemove(toast.id)}
        className="opacity-50 hover:opacity-100 transition-opacity"
      >
        ×
      </button>
    </div>
  );
}
