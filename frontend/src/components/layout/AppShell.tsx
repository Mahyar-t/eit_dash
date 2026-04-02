import { useEffect, useMemo, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';

import logo from '../../assets/logo.png';
import { ProcessStepper } from './ProcessStepper';
import { Sidebar } from './Sidebar';
import { TopNavbar } from './TopNavbar';

const shellHiddenPaths = new Set(['/', '/about', '/contact']);

export function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const showDashboardShell = useMemo(() => !shellHiddenPaths.has(location.pathname), [location.pathname]);

  useEffect(() => {
    const HIDE_AFTER_SCROLL_Y = 96;
    const DELTA_THRESHOLD = 10;

    let ticking = false;
    let lastScrollY = window.scrollY || 0;
    let lastAppliedState: boolean | null = null;

    const setNavbarHidden = (hidden: boolean) => {
      if (lastAppliedState === hidden) {
        return;
      }

      document.body.classList.toggle('navbar-hidden', hidden);
      lastAppliedState = hidden;
    };

    const updateNavbar = () => {
      const currentScrollY = window.scrollY || 0;
      const delta = currentScrollY - lastScrollY;

      if (currentScrollY <= HIDE_AFTER_SCROLL_Y) {
        setNavbarHidden(false);
      } else if (Math.abs(delta) >= DELTA_THRESHOLD) {
        setNavbarHidden(delta > 0);
      }

      lastScrollY = currentScrollY;
      ticking = false;
    };

    const handleScroll = () => {
      if (ticking) {
        return;
      }

      ticking = true;
      window.requestAnimationFrame(updateNavbar);
    };

    const resetNavbar = () => {
      lastScrollY = window.scrollY || 0;
      setNavbarHidden(false);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('popstate', resetNavbar);
    window.addEventListener('hashchange', resetNavbar);

    resetNavbar();

    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('popstate', resetNavbar);
      window.removeEventListener('hashchange', resetNavbar);
      document.body.classList.remove('navbar-hidden');
    };
  }, []);

  useEffect(() => {
    document.body.classList.remove('navbar-hidden');
  }, [location.pathname]);

  return (
    <div className={showDashboardShell ? 'app-root' : 'app-root app-root--shell-hidden'}>
      <TopNavbar onOpenSidebar={() => setSidebarOpen(true)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="app-shell">
        {showDashboardShell ? (
          <div id="dashboard-shell">
            <div className="app-header">
              <div className="app-brand">
                <h1 className="app-title">EIT Dashboard</h1>
                <p className="app-subtitle">
                  A local workflow for loading, preparing, and analyzing EIT data. Loaded datasets and selections will
                  appear across all modules as you progress through the tab steps.
                </p>
              </div>
            </div>
            <ProcessStepper />
          </div>
        ) : null}

        <div className="app-page-wrapper">
          <Outlet />
        </div>
      </div>

      <footer className="app-footer" id="app-footer">
        <img src={logo} alt="ROTARC Research Group" className="footer-logo" />
        <span className="footer-copy">© 2026 ROTARC Research Group. All Rights Reserved.</span>
      </footer>
    </div>
  );
}
