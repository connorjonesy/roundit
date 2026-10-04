import './style.css';
import { MapLibreMapComponent } from './mapLibre';

const map = new MapLibreMapComponent({
    target: '#map',
    style: 'https://tiles.openfreemap.org/styles/liberty',

    // Start in Vancouver
    center: [-123.1207, 49.2827],
    zoom: 12,

    // Restrict navigation to the Vancouver area
    maxBounds: [
        [-123.30, 49.18], // Southwest
        [-122.90, 49.35]  // Northeast
    ],

    minZoom: 10,
    maxZoom: 19
});