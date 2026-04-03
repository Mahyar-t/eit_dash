import { NavLink } from "react-router-dom";

import { topNavLinks } from "../../data/navigation";

type SidebarProps = {
  isOpen: boolean;
  onClose: () => void;
};

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      <button
        type="button"
        className={
          isOpen
            ? "sidebar-backdrop sidebar-backdrop--open"
            : "sidebar-backdrop"
        }
        onClick={onClose}
        aria-label="Close navigation menu"
      />
      <aside
        className={isOpen ? "main-sidebar main-sidebar--open" : "main-sidebar"}
      >
        <div className="glass-panel sidebar-panel">
          <div className="sidebar-main">
            <div className="sidebar-header">
              <div className="sidebar-brand">
                <p className="sidebar-eyebrow">Navigation</p>
                <h2>Welcome to ALIVE</h2>
              </div>
              <button
                type="button"
                className="sidebar-close"
                onClick={onClose}
                aria-label="Close sidebar"
              >
                <span aria-hidden="true">×</span>
              </button>
            </div>
            <p className="page-intro sidebar-copy">
              Advanced Lung Image processing for personalized mechanical
              VEntilation dashboard for loading, pre-processing, and analyzing
              EIT data.
            </p>
            <div className="sidebar-divider" />
            <p className="sidebar-section-label">Explore</p>
            {topNavLinks.map((link) => (
              <NavLink
                key={link.path}
                to={link.path}
                onClick={onClose}
                className={({ isActive }) =>
                  isActive
                    ? "sidebar-nav-link sidebar-nav-link--block active"
                    : "sidebar-nav-link sidebar-nav-link--block"
                }
              >
                <span className="sidebar-nav-link__text">{link.label}</span>
                <span className="sidebar-nav-link__chevron" aria-hidden="true">
                  ›
                </span>
              </NavLink>
            ))}
          </div>
          <div className="sidebar-bottom">
            <div className="sidebar-footer-note">
              <span className="sidebar-footer-note__dot" />
              <span>Local workflow, local data.</span>
            </div>
            <a
              href="https://github.com/EIT-ALIVE/eit_dash"
              target="_blank"
              rel="noreferrer"
              className="sidebar-github-link"
            >
              <span className="sidebar-github-link__label">
                GitHub repository
              </span>
            </a>
          </div>
        </div>
      </aside>
    </>
  );
}
