import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

export interface MapLibreMapComponentOptions
    extends Partial<maplibregl.MapOptions> {
    target: string | HTMLElement;
}

export class MapLibreMapComponent {
    public readonly map: maplibregl.Map;

    constructor({
        target,
        style = 'https://tiles.openfreemap.org/styles/liberty',
        center = [-122.9805, 49.2488],
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
            new maplibregl.NavigationControl(),
            'top-right'
        );

        this.map.addControl(
            new maplibregl.ScaleControl(),
            'bottom-left'
        );
    }
}