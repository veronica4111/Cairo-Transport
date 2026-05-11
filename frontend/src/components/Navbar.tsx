import { useState } from "react";
import { Bell, Settings, Moon, Sun } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export default function Navbar({ activeTab, onTabChange }: NavbarProps) {
  const [alerts] = useState(3);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const tabs = ["NETWORK MAP", "ML MODEL", "RACE VIEW"];

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    // Dispatch custom event for other components to listen to
    window.dispatchEvent(new CustomEvent('darkModeToggle', { detail: { isDark: !isDarkMode } }));
  };

  return (
    <nav className="flex items-center justify-between h-14 px-6 border-b border-border-primary bg-bg-primary/80 backdrop-blur-md sticky top-0 z-50">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-teal shadow-[0_0_12px_var(--color-teal)]"></span>
        </div>
        <span className="font-mono font-bold text-sm tracking-widest text-teal">
          CAIRO_COMMAND_CENTER
        </span>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => onTabChange(tab)}
            className={`px-4 py-2 text-xs font-medium tracking-wider rounded-md transition-all duration-300 ${
              activeTab === tab
                ? "text-teal bg-teal/10 shadow-[inset_0_-2px_0_var(--color-teal)]"
                : "text-text-secondary hover:text-text-primary hover:bg-bg-secondary/50"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Right icons */}
      <div className="flex items-center gap-5">
        {/* Dark Mode Toggle */}
        <button 
          onClick={toggleDarkMode}
          className="p-1.5 text-text-secondary hover:text-teal transition-colors relative group" 
          title={isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
          <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-bg-secondary text-text-primary text-[10px] rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            {isDarkMode ? "Light Mode" : "Dark Mode"}
          </span>
        </button>
        
        {/* Alerts */}
        <button className="relative p-1.5 text-text-secondary hover:text-teal transition-colors" title="Alerts">
          <Bell size={18} />
          {alerts > 0 && (
            <span className="absolute top-0 right-0 w-4 h-4 rounded-full text-[10px] font-bold flex items-center justify-center bg-red text-white shadow-[0_0_8px_var(--color-red)] border border-bg-primary">
              {alerts}
            </span>
          )}
        </button>
        {/* Settings */}
        <button className="p-1.5 text-text-secondary hover:text-teal transition-colors" title="Settings">
          <Settings size={18} />
        </button>
        {/* Profile */}
        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold bg-teal/20 text-teal border border-teal/40 shadow-[0_0_10px_var(--color-teal-glow)] cursor-pointer hover:bg-teal/30 transition-colors">
          CC
        </div>
      </div>
    </nav>
  );
}
