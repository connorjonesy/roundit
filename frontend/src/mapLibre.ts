import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapNavigation } from './ui/mapControls';

// Configure the MapLibre worker for Vite
maplibregl.setWorkerUrl(workerUrl);

export interface MapLibreMapComponentOptions
    extends Partial<maplibregl.MapOptions> {
    target: string | HTMLElement;
}

export class MapLibreMapComponent {
    public readonly map: maplibregl.Map;

    constructor({
        target,
        style = 'https://tiles.openfreemap.org/styles/liberty',
        center = [-123.1207, 49.2827],
        zoom = 12,
        ...mapOptions
    }: MapLibreMapComponentOptions) {

        // Find the HTML element
        const mountNode = typeof target === 'string'
            ? document.querySelector<HTMLElement>(target)
            : target;

        if (!mountNode) {
            throw new Error('Map target not found');
        }

        // Initialize MapLibre directly inside the element
        this.map = new maplibregl.Map({
            container: mountNode,
            style,
            center,
            zoom,
            ...mapOptions
        });

        // Add map controls
        this.map.addControl(
            new MapNavigation(),
            'top-right'
        );

        this.map.addControl(
            new maplibregl.ScaleControl(),
            'bottom-left'
        );

        // Debug map loading
        this.map.on('load', () => {
            console.log('Map loaded successfully!');
        });

        this.map.on('error', (e) => {
            console.error('MapLibre error:', e.error);
        });
    }
}
