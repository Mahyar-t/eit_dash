import { Link, NavLink, useLocation } from 'react-router-dom';

import logoUp from '../../assets/logo_up.png';
import { topNavLinks } from '../../data/navigation';

type TopNavbarProps = {
  onOpenSidebar: () => void;
};

export function TopNavbar({ onOpenSidebar }: TopNavbarProps) {
  const location = useLocation();
  const dashboardPaths = new Set(['/load', '/preprocessing', '/analyze']);

  return (
    <nav className="top-navbar" id="top-navbar">
      <button className="menu-button" type="button" onClick={onOpenSidebar} aria-label="Open navigation menu">
        <span />
        <span />
        <span />
      </button>
      <Link to="/" className="app-logo-text">
        <img src={logoUp} alt="EIT-ALIVE" className="app-logo-img" />
        <span>EIT-ALIVE</span>
      </Link>
      <div className="top-navbar__links">
        {topNavLinks.map((link) => (
          <NavLink
            key={link.path}
            to={link.path}
            className={({ isActive }) =>
              isActive || (link.label === 'Dashboard' && dashboardPaths.has(location.pathname))
                ? 'nav-text-link active'
                : 'nav-text-link'
            }
          >
            {link.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
