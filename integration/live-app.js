/* Live wrapper around the LOCKED frontend's <App/> (frontend/src/App.js —
 * never edited). The "@/App$" alias in integration/craco.config.js resolves
 * index.js's `import App from "@/App"` to this module, which renders the real
 * App unchanged but subscribes to integration/live-data.js: whenever a fresh
 * bootstrap payload lands, the tree re-renders in place (no remount, no
 * reload) and every page reads the updated data on its normal render path.
 * Zero visual/behavioral difference beyond the data staying current.
 *
 * CommonJS + React.createElement on purpose: files outside frontend/src are
 * not JSX-transformed by CRA's babel pipeline. */
var React = require("react");
var App = require("../frontend/src/App").default;
var liveData = require("./live-data.js");

exports.__esModule = true;
exports.default = function LiveApp() {
  React.useSyncExternalStore(liveData.subscribe, liveData.getVersion);
  return React.createElement(App, null);
};
