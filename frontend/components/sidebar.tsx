import { BookOpen, Clock3, Database, LayoutGrid, Network, Search, Settings2 } from "lucide-react";

import { BrandMark } from "./brand";

const navigation = [
  { label: "Memory", icon: LayoutGrid, active: true },
  { label: "Explore", icon: Search },
  { label: "Timeline", icon: Clock3 },
  { label: "Relationships", icon: Network },
];

export function Sidebar({ repository }: { repository: string }) {
  return (
    <aside className="sidebar">
      <BrandMark />
      <div className="workspace-switcher">
        <span className="workspace-sigil">A</span>
        <span>
          <strong>Atlas</strong>
          <small>{repository}</small>
        </span>
      </div>
      <nav aria-label="Chronicle navigation">
        <p className="nav-label">Workspace</p>
        {navigation.map(({ label, icon: Icon, active }) => (
          <button className={`nav-item ${active ? "active" : ""}`} key={label} type="button">
            <Icon size={16} strokeWidth={1.7} />
            {label}
          </button>
        ))}
      </nav>
      <nav className="sidebar-bottom" aria-label="Workspace tools">
        <button className="nav-item" type="button">
          <Database size={16} strokeWidth={1.7} />
          Storage
        </button>
        <button className="nav-item" type="button">
          <BookOpen size={16} strokeWidth={1.7} />
          Playbook
        </button>
        <button className="nav-item" type="button">
          <Settings2 size={16} strokeWidth={1.7} />
          Settings
        </button>
      </nav>
    </aside>
  );
}
