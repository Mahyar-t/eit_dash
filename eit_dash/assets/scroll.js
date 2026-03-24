(function () {
  const HIDE_AFTER_SCROLL_Y = 96;
  const DELTA_THRESHOLD = 10;

  let ticking = false;
  let lastScrollY = window.scrollY || 0;
  let lastAppliedState = null;

  function setNavbarHidden(hidden) {
    if (lastAppliedState === hidden) {
      return;
    }

    document.body.classList.toggle("navbar-hidden", hidden);
    lastAppliedState = hidden;
  }

  function updateNavbar() {
    const currentScrollY = window.scrollY || 0;
    const delta = currentScrollY - lastScrollY;

    if (currentScrollY <= HIDE_AFTER_SCROLL_Y) {
      setNavbarHidden(false);
    } else if (Math.abs(delta) >= DELTA_THRESHOLD) {
      setNavbarHidden(delta > 0);
    }

    lastScrollY = currentScrollY;
    ticking = false;
  }

  function handleScroll() {
    if (ticking) {
      return;
    }

    ticking = true;
    window.requestAnimationFrame(updateNavbar);
  }

  function resetNavbar() {
    lastScrollY = window.scrollY || 0;
    setNavbarHidden(false);
  }

  window.addEventListener("scroll", handleScroll, { passive: true });
  window.addEventListener("popstate", resetNavbar);
  window.addEventListener("hashchange", resetNavbar);
  window.addEventListener("load", resetNavbar);

  resetNavbar();
})();
