import './ui/vanilla';
import './style.css';
import { MapLibreMapComponent } from './mapLibre';
import { addIntersectionLayers } from './intersectionLayers';

const map = new MapLibreMapComponent({
    target: '#map',
    style: 'https://tiles.openfreemap.org/styles/liberty',

    // Start with a province-wide view of British Columbia.
    center: [-124.5, 54.5],
    zoom: 5,

    // Restrict navigation to British Columbia.
    maxBounds: [
        [-139.1, 48.2], // Southwest: [west, south]
        [-114.0, 60.1]  // Northeast: [east, north]
    ],

    minZoom: 4,
    maxZoom: 19
});

map.map.on('load', () => {
    void addIntersectionLayers(map.map);
});
