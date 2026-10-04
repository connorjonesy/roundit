/** Keep popup markup separate from map styling and event handling. */
export function createIntersectionPopup(properties: Record<string, unknown>, close: () => void) {
    const content = document.createElement('div');
    content.className = 'intersection-popup';
    content.innerHTML = `
        <vanilla-card class="ui-card popup-card">
            <card-header class="ui-card-header popup-header">
                <h3 class="popup-title"></h3>
                <vanilla-button type="button" variant="ghost" size="icon" data-close-popup aria-label="Close intersection details">×</vanilla-button>
            </card-header>
            <card-content class="ui-card-content">
                <p class="popup-period muted-text"></p>
                <dl class="popup-metrics"></dl>
                <p class="map-note">Pedestrian and cyclist counts may overlap.</p>
                <p class="shared-location map-note" hidden>Other named intersections share this location.</p>
            </card-content>
        </vanilla-card>
    `;
    // Source text is assigned as text, never interpolated into HTML.
    content.querySelector('.popup-title')!.textContent = String(properties.name);
    content.querySelector('.popup-period')!.textContent = `Records span ${properties.period_start_year}–${properties.period_end_year}`;
    const metrics = content.querySelector('dl')!;
    for (const [label, key] of [['Reported crashes', 'total_crashes'], ['Pedestrian-involved', 'pedestrian_crashes'], ['Cyclist-involved', 'cyclist_crashes']]) {
        const term = document.createElement('dt');
        const value = document.createElement('dd');
        term.textContent = label!;
        value.textContent = Number(properties[key!]).toLocaleString();
        metrics.append(term, value);
    }
    const shared = properties.shared_coordinate === true || properties.shared_coordinate === 'true';
    (content.querySelector('.shared-location') as HTMLElement).hidden = !shared;
    content.addEventListener('click', event => {
        if ((event.target as Element).closest('button[data-close-popup]')) close();
    });
    return content;
}
