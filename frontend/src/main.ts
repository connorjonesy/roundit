import './ui/vanilla';
import './style.css';
import { MapLibreMapComponent } from './mapLibre';
import { addIntersectionLayers } from './intersectionLayers';

const map = new MapLibreMapComponent({
    target: '#map',
    style: 'https://tiles.openfreemap.org/styles/liberty',

    // Start in Vancouver
    center: [-123.1207, 49.2827],
    zoom: 12,

    // Restrict navigation to the Vancouver area
    maxBounds: [
        [-123.46, 48.98], // Southwest: [west, south]
        [-122.38, 49.59]  // Northeast: [east, north]
    ],

    minZoom: 10,
    maxZoom: 19
});

map.map.on('load', () => {
    void addIntersectionLayers(map.map);
});
