/**
 * Smooth page transition handler for EIT-ALIVE Dashboard.
 *
 * This implementation avoids CSS @keyframes remount jitter.
 * On any internal link click, we:
 *  1. Determine if it's a full page transition (to/from index) or a tab switch.
 *  2. Add `.page-transitioning` or `.tab-transitioning` to setup the smooth CSS transitions.
 *  3. Add `.page-fading-out` or `.tab-fading-out` to `.app-shell`.
 *  4. After the fade out duration, we swap to the rendering state.
 *  5. Let Dash navigate natively.
 *  6. Observe the DOM to remove the rendering state, letting the
 *     default smooth CSS transitions handle the fade-in cleanly.
 *  7. After the fade-in fully completes, remove the transitioning setup classes so
 *     that `transform` and `opacity` properties don't override `backdrop-filter` glassmorphism.
 */
(function () {
  const FADE_OUT_MS = 20;
  const FADE_IN_MS = 20;

  const TAB_FADE_OUT_MS = 20;
  const TAB_FADE_IN_MS = 20;

  function isInternalHref(href) {
    if (!href) return false;
    try {
      const url = new URL(href, window.location.origin);
      return url.origin === window.location.origin;
    } catch (_) {
      return false;
    }
  }

  document.addEventListener(
    "click",
    function (e) {
      let target = e.target;
      while (target && target !== document) {
        if (
          target.tagName === "A" &&
          isInternalHref(target.getAttribute("href"))
        ) {
          const href = target.getAttribute("href");
          if (!e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) {
            const destUrl = new URL(href, window.location.origin);
            const currentPath = window.location.pathname;
            const destPath = destUrl.pathname;

            // Allow default behavior for hash links / same page
            if (currentPath === destPath) {
              return;
            }

            e.preventDefault();
            const shell = document.querySelector(".app-shell");

            if (!shell) {
              window.history.pushState({}, "", href);
              window.dispatchEvent(
                new PopStateEvent("popstate", { state: {} }),
              );
              return;
            }

            // Determine transition type:
            const isFullPageTransition =
              currentPath === "/" || destPath === "/";

            const transitionClass = isFullPageTransition
              ? "page-transitioning"
              : "tab-transitioning";
            const fadeOutClass = isFullPageTransition
              ? "page-fading-out"
              : "tab-fading-out";
            const renderingClass = isFullPageTransition
              ? "page-rendering"
              : "tab-rendering";

            const fadeOutDelay = isFullPageTransition
              ? FADE_OUT_MS
              : TAB_FADE_OUT_MS;
            const fadeInDelay = isFullPageTransition
              ? FADE_IN_MS
              : TAB_FADE_IN_MS;

            // Trigger smooth fade out
            shell.classList.add(transitionClass);
            shell.classList.add(fadeOutClass);

            setTimeout(function () {
              // Now invisible. Snap to start-render position instantly.
              shell.classList.remove(fadeOutClass);
              shell.classList.add(renderingClass);

              // Tell Dash to navigate
              window.history.pushState({}, "", href);
              window.dispatchEvent(
                new PopStateEvent("popstate", { state: {} }),
              );

              const wrapper = document.querySelector(".app-page-wrapper");

              function finishTransition() {
                // Double RAF guarantees the browser has painted the rendering state
                // before we remove it to trigger the CSS transition
                requestAnimationFrame(() => {
                  requestAnimationFrame(() => {
                    shell.classList.remove(renderingClass);

                    // Once the fade-in finishes smoothly via CSS, remove the setup class
                    // so the elements lose the explicit stacking context created by `transform`
                    setTimeout(() => {
                      shell.classList.remove(transitionClass);
                    }, fadeInDelay + 50); // slight buffer
                  });
                });
              }

              if (wrapper) {
                // Wait for Dash's React to update the DOM
                let observer = new MutationObserver(function () {
                  observer.disconnect();
                  finishTransition();
                });
                observer.observe(wrapper, { childList: true, subtree: true });

                // Safety fallback if page content doesn't change
                setTimeout(function () {
                  observer.disconnect();
                  finishTransition();
                }, 600);
              } else {
                finishTransition();
              }
            }, fadeOutDelay);
          }
          break;
        }
        target = target.parentElement;
      }
    },
    true,
  );
})();
