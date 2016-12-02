// Setup notebook base URL
__webpack_public_path__ = document.querySelector('body').getAttribute('data-base-url') + 'nbextensions/jupyter-vizic/';

// Load css
require('leaflet/leaflet.css');
require('leaflet/css/L.Control.MousePosition.css');
require('leaflet-fullscreen/dist/leaflet.fullscreen.css');
require('leaflet-draw/dist/leaflet.draw.css');
require('./jupyter-vizic.css');

// Forcibly load the marker icon images to be in the bundle.
require('leaflet/images/marker-shadow.png');
require('leaflet/images/marker-icon.png');
require('leaflet/images/marker-icon-2x.png');
require('leaflet-fullscreen/dist/fullscreen.png');
require('leaflet-fullscreen/dist/fullscreen@2x.png');

// Export everything from jupyter-leaflet and the npm package version number.
module.exports = require('./jupyter-vizic.js');
module.exports['version'] = require('../package.json').version;
