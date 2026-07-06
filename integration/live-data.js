/**
 * FanPulse integration data module.
 *
 * The locked frontend (frontend/src — NEVER edited) imports all of its data
 * from "@/data/mock". When the app is launched through
 * integration/craco.config.js, that import is aliased to THIS module, which
 * loads the same datasets from the real FanPulse backend instead.
 *
 * Every export name and shape below matches frontend/src/data/mock.js 1:1.
 * The request is synchronous on purpose: the UI reads these exports at
 * module-evaluation time (before the first React render), so the data must
 * exist before index.js runs. One blocking XHR at page load against
 * localhost is the price of keeping the frontend 100% untouched.
 *
 * Launch: scripts/run_frontend.ps1|.sh  (backend must be up on :8000 —
 * scripts/run_backend.ps1|.sh — or the page fails loudly with instructions.)
 */

var API_BASE =
  (typeof window !== "undefined" && window.__FANPULSE_API_URL__) ||
  "http://localhost:8000";

function loadBootstrap() {
  var xhr = new XMLHttpRequest();
  // Synchronous: must resolve before the app's first render (see header).
  xhr.open("GET", API_BASE + "/api/v1/ui/bootstrap", false);
  try {
    xhr.send(null);
  } catch (e) {
    throw new Error(
      "[FanPulse] Could not reach the backend at " + API_BASE + ".\n" +
      "Start it first:  scripts/run_backend.ps1  (or ./scripts/run_backend.sh)\n" +
      "Original error: " + e.message
    );
  }
  if (xhr.status !== 200) {
    throw new Error(
      "[FanPulse] Backend bootstrap failed: HTTP " + xhr.status + " from " +
      API_BASE + "/api/v1/ui/bootstrap — " + xhr.responseText.slice(0, 300)
    );
  }
  return JSON.parse(xhr.responseText);
}

var data = loadBootstrap();

/* eslint-disable no-console */
console.info(
  "[FanPulse] Live backend data loaded (" + API_BASE + "), generated at " +
  data.generated_at + " — demo match " + data.demo_match_id
);

// CommonJS on purpose: this file sits outside frontend/src, so CRA's babel
// pipeline for "external" files handles it; webpack 5 statically maps these
// to named ESM exports, so the locked UI's `import { X } from "@/data/mock"`
// resolves exactly as it does against the original mock module.
exports.BRAND = data.brand;
exports.NAV_LINKS = data.nav_links;
exports.KPI_TICKER = data.kpi_ticker;
exports.FEATURES = data.features;
exports.FAN_SEGMENTS = data.fan_segments;
exports.COUNTRIES = data.countries;
exports.INDUSTRIES = data.industries;
exports.LOCATIONS = data.locations;
exports.STRATEGIES = data.strategies;
exports.MATCHES = data.matches;
exports.SENTIMENT_TIMELINE = data.sentiment_timeline;
exports.MOMENTS = data.moments;
exports.TRENDING = data.trending;
