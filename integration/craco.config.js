/**
 * External CRACO config — the integration seam that wires the LOCKED frontend
 * to the real backend without touching a single file inside frontend/.
 *
 * How it works:
 *   - loads frontend/craco.config.js (the locked app's own config) untouched;
 *   - adds ONE exact-match webpack alias: the request "@/data/mock" (the UI's
 *     single data module) resolves to integration/live-data.js, which loads
 *     identical dataset shapes from the backend's /api/v1/ui/bootstrap;
 *   - drops CRA's ModuleScopePlugin, which would otherwise forbid importing a
 *     module that lives outside frontend/src (live-data.js deliberately does —
 *     frontend/ is locked).
 *
 * Launch (from frontend/, where react-scripts must run):
 *   npx craco start --config ../integration/craco.config.js
 * Running plain `yarn start` inside frontend/ still uses the original mock
 * data module — the friend's app remains fully intact and standalone.
 */
const path = require("path");

const baseConfig = require(path.resolve(__dirname, "..", "frontend", "craco.config.js"));
const liveData = path.resolve(__dirname, "live-data.js");

const baseWebpack = baseConfig.webpack || {};
const baseConfigure = baseWebpack.configure;

module.exports = {
  ...baseConfig,
  webpack: {
    ...baseWebpack,
    alias: {
      // "$" = exact match: only the "@/data/mock" request is redirected;
      // every other "@/..." import keeps resolving into frontend/src.
      // MUST come before the base "@" prefix alias — webpack applies alias
      // entries in insertion order and stops at the first match.
      "@/data/mock$": liveData,
      ...(baseWebpack.alias || {}),
    },
    configure: (webpackConfig, context) => {
      if (typeof baseConfigure === "function") {
        webpackConfig = baseConfigure(webpackConfig, context) || webpackConfig;
      } else if (baseConfigure && typeof baseConfigure === "object") {
        webpackConfig = { ...webpackConfig, ...baseConfigure };
      }
      if (webpackConfig.resolve && Array.isArray(webpackConfig.resolve.plugins)) {
        webpackConfig.resolve.plugins = webpackConfig.resolve.plugins.filter(
          (p) => !(p && p.constructor && p.constructor.name === "ModuleScopePlugin")
        );
      }
      return webpackConfig;
    },
  },
};
