import type { IControl, Map } from 'maplibre-gl';

/** Use Vanilla UI buttons while MapLibre owns map movement and positioning. */
export class MapNavigation implements IControl {
    private container?: HTMLDivElement;
    private map?: Map;

    onAdd(map: Map) {
        this.map = map;
        this.container = document.createElement('div');
        this.container.className = 'maplibregl-ctrl map-navigation';
        this.container.setAttribute('role', 'group');
        this.container.setAttribute('aria-label', 'Map navigation');
        this.container.innerHTML = `
            <vanilla-button type="button" variant="outline" size="icon" data-action="in" aria-label="Zoom in" title="Zoom in">+</vanilla-button>
            <vanilla-button type="button" variant="outline" size="icon" data-action="out" aria-label="Zoom out" title="Zoom out">−</vanilla-button>
            <vanilla-button type="button" variant="outline" size="icon" data-action="north" aria-label="Reset bearing and pitch" title="Reset bearing and pitch">N</vanilla-button>
        `;
        // Delegate from the stable container because Vanilla UI replaces its tags.
        this.container.addEventListener('click', event => {
            const action = (event.target as Element).closest<HTMLButtonElement>('button[data-action]')?.dataset.action;
            if (action === 'in') map.zoomIn();
            if (action === 'out') map.zoomOut();
            if (action === 'north') map.resetNorthPitch();
        });
        map.on('zoom', this.updateButtons);
        return this.container;
    }

    private updateButtons = () => {
        if (!this.map || !this.container) return;
        const zoom = this.map.getZoom();
        const zoomIn = this.container.querySelector<HTMLButtonElement>('[data-action="in"]');
        const zoomOut = this.container.querySelector<HTMLButtonElement>('[data-action="out"]');
        if (zoomIn) zoomIn.disabled = zoom >= this.map.getMaxZoom();
        if (zoomOut) zoomOut.disabled = zoom <= this.map.getMinZoom();
    };

    onRemove() {
        this.map?.off('zoom', this.updateButtons);
        this.container?.remove();
        this.map = undefined;
    }
}
