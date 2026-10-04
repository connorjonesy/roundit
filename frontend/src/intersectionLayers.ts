import { Popup } from 'maplibre-gl';
import type { Map } from 'maplibre-gl';
import type { FeatureCollection, Point } from 'geojson';
import { getLayerControls } from './ui/layerControls';
import { createIntersectionPopup } from './ui/intersectionPopup';

export async function addIntersectionLayers(map: Map) {
    const status = document.querySelector<HTMLElement>('#data-status')!;
    const controls = getLayerControls();
    const popup = new Popup({ maxWidth: '340px', closeButton: false });
    controls.setDisabled(true);
    try {
        const response = await fetch(`${import.meta.env.BASE_URL}data/intersections.geojson`);
        if (!response.ok) throw new Error(`Data request failed (${response.status})`);
        const data: FeatureCollection<Point> = await response.json();
        if (data.type !== 'FeatureCollection' || !data.features?.length) throw new Error('No intersection data');
        const properties = data.features.map(feature => feature.properties!);
        const firstYear = Math.min(...properties.map(p => Number(p.period_start_year)));
        const lastYear = Math.max(...properties.map(p => Number(p.period_end_year)));
        const maxCount = Math.max(...properties.map(p => Number(p.total_crashes)));
        map.addSource('intersections', { type: 'geojson', data });
        // Preserve street labels above our overlays.
        const firstLabel = map.getStyle().layers?.find(layer => layer.type === 'symbol')?.id;
        map.addLayer({
            id: 'intersection-heatmap', type: 'heatmap', source: 'intersections', maxzoom: 17,
            paint: {
                // Square-root weights keep large counts from overwhelming smaller locations.
                'heatmap-weight': ['/', ['sqrt', ['get', 'total_crashes']], Math.sqrt(maxCount)],
                'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 10, 0.8, 15, 2],
                'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 10, 16, 15, 30],
                'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'],
                    0, 'rgba(33,102,172,0)', 0.15, '#2196c4', 0.4, '#64d5b2',
                    0.65, '#ffe16b', 0.85, '#f46d43', 1, '#b2182b'],
                'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 10, 0.75, 14, 0.65, 17, 0]
            }
        }, firstLabel);
        map.addLayer({
            id: 'intersection-points', type: 'circle', source: 'intersections',
            paint: {
                'circle-radius': ['interpolate', ['linear'], ['get', 'total_crashes'],
                    1, 3, 25, 4, 100, 6, 500, 9, 1200, 12],
                'circle-color': ['interpolate', ['linear'], ['get', 'total_crashes'],
                    1, '#2196c4', 25, '#ffe16b', 100, '#f46d43', 500, '#b2182b'],
                'circle-opacity': ['interpolate', ['linear'], ['zoom'], 10, 0, 12, 0.15, 14, 0.8, 16, 0.95],
                'circle-stroke-color': '#ffffff', 'circle-stroke-width': 1,
                'circle-stroke-opacity': ['interpolate', ['linear'], ['zoom'], 10, 0, 12, 0.15, 14, 0.9]
            }
        }, firstLabel);
        const updateVisibility = () => {
            const { heat, points } = controls.state();
            map.setLayoutProperty('intersection-heatmap', 'visibility', heat ? 'visible' : 'none');
            map.setLayoutProperty('intersection-points', 'visibility', points ? 'visible' : 'none');
            map.setPaintProperty('intersection-points', 'circle-opacity', heat
                ? ['interpolate', ['linear'], ['zoom'], 10, 0, 12, 0.15, 14, 0.8, 16, 0.95] : 0.85);
            map.setPaintProperty('intersection-points', 'circle-stroke-opacity', heat
                ? ['interpolate', ['linear'], ['zoom'], 10, 0, 12, 0.15, 14, 0.9] : 0.9);
            popup.remove();
            map.getCanvas().style.cursor = '';
        };
        controls.onChange(updateVisibility);
        updateVisibility();
        map.on('mouseenter', 'intersection-points', () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', 'intersection-points', () => { map.getCanvas().style.cursor = ''; });
        map.on('click', 'intersection-points', event => {
            const feature = event.features?.[0];
            if (!feature || feature.geometry.type !== 'Point') return;
            const content = createIntersectionPopup(feature.properties, () => popup.remove());
            popup.setLngLat(feature.geometry.coordinates as [number, number]).setDOMContent(content).addTo(map);
        });
        status.textContent = `${data.features.length.toLocaleString()} named intersections · ${firstYear}–${lastYear}`;
        controls.setDisabled(false);
    } catch (error) {
        console.error('Intersection layer could not load:', error);
        status.textContent = 'Intersection data could not load. Refresh to try again.';
        status.classList.add('load-error');
    }
}
