window.dash_clientside = Object.assign({}, window.dash_clientside, {
  playback: {
    control_animation: function (n_play, n_reset, is_playing, graph_id) {
      const triggered = window.dash_clientside.callback_context.triggered;
      if (!triggered || triggered.length === 0) {
        return window.dash_clientside.no_update;
      }

      const prop = triggered[0].prop_id;
      const frameOptions = {
        frame: { duration: 80, redraw: true },
        fromcurrent: true,
        transition: { duration: 0 },
      };

      // Dash stores the pattern-matching ID on the Graph wrapper, not on the
      // inner Plotly node used by Plotly.animate().
      let graphDiv = null;
      for (const wrapper of document.querySelectorAll(".dash-graph[id]")) {
        try {
          const gid = JSON.parse(wrapper.id);
          if (
            gid.type === graph_id.type &&
            String(gid.period) === String(graph_id.period) &&
            gid.label === graph_id.label
          ) {
            graphDiv = wrapper.querySelector(".js-plotly-plot");
            break;
          }
        } catch (e) {
          /* non-JSON id element, skip */
        }
      }

      if (!graphDiv || typeof Plotly === "undefined") {
        return [is_playing, is_playing ? "⏸️ Pause" : "▶️ Play"];
      }

      // --- Reset: jump to frame 0 and stop ---
      if (prop.includes("reset")) {
        Plotly.animate(graphDiv, [], {
          frame: { duration: 0, redraw: false },
          mode: "immediate",
          transition: { duration: 0 },
        });
        Plotly.animate(graphDiv, ["frame-0"], {
          frame: { duration: 0, redraw: true },
          mode: "immediate",
          transition: { duration: 0 },
        });
        return [false, "▶️ Play"];
      }

      // --- Play / Pause toggle ---
      const nowPlaying = !is_playing;
      if (nowPlaying) {
        Plotly.animate(graphDiv, null, frameOptions);
      } else {
        Plotly.animate(graphDiv, [], {
          frame: { duration: 0, redraw: false },
          mode: "immediate",
          transition: { duration: 0 },
        });
      }

      return [nowPlaying, nowPlaying ? "⏸️ Pause" : "▶️ Play"];
    },
  },
});
