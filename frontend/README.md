# Intersection map

## Frontend structure

```text
index.html                       Sidebar markup using Vanilla UI components
src/
  main.ts                        Registers UI, creates map, loads intersection layers
  mapLibre.ts                    MapLibre setup, navigation, scale, map events
  intersectionLayers.ts          GeoJSON loading and heatmap/point behavior
  style.css                      Imports the four CSS files below
  styles/
    theme.css                    Shared colors, font, border radius, sidebar width
    components.css               Card, label, and switch appearance
    layout.css                   Sidebar/map layout and mobile sizing
    map.css                      Legend, navigation, popup, scale appearance
  ui/
    vanilla.ts                   Vanilla UI registration and switch event adapter
    vanilla-ui.d.ts              Types missing from the published library
    layerControls.ts             Read switch state and enable/disable layer controls
    mapControls.ts               Vanilla UI zoom and reset-bearing/pitch buttons
    intersectionPopup.ts         Intersection detail card markup
scripts/export_intersections.py  CSV-to-GeoJSON export
```

## Editing the UI

We use `@vanilla-primitives/styled` from [Vanilla UI](https://www.vanilla-ui.com/docs/introduction).
Cards, labels, switches, and buttons are registered in `src/ui/vanilla.ts` before
the application starts. There is no React or Tailwind setup. Buttons use Vanilla
UI's plain CSS preset. Cards, labels, and switches use the library's components
with explicit, readable `.ui-*` CSS rules instead of its Tailwind utility classes.

**Change the theme:** edit `src/styles/theme.css`. For example:

```css
:root {
  --primary: 193 74% 34%; /* Hue, saturation, lightness; used by buttons/switches */
  --radius: 0.75rem;     /* Card and button rounding */
  --sidebar-width: 400px;
}
```

These colors contain HSL channels, not hex strings. Use `hsl(var(--primary))` when
referencing them in your own CSS. Heatmap colors are a separate data palette in
`intersectionLayers.ts` and the legend in `styles/map.css`.

**Change sidebar content:** edit `index.html`. A card looks like:

```html
<vanilla-card class="ui-card">
  <card-header class="ui-card-header">
    <card-title class="ui-card-title"><h2>Your section</h2></card-title>
  </card-header>
  <card-content class="ui-card-content">
    <p>Your content</p>
    <vanilla-button type="button" variant="outline">Your action</vanilla-button>
  </card-content>
</vanilla-card>
```

**Add a layer switch:** copy a `.layer-row` in `index.html`, give its label and
switch matching `for`/`id` values, then wire its behavior in `layerControls.ts`
and `intersectionLayers.ts`. The state is read from `aria-checked`.

**Edit a popup:** change `src/ui/intersectionPopup.ts` for its content and
`src/styles/map.css` for appearance. Source values are set with `textContent`
so street names cannot introduce HTML.

**Add another component:** import its implementation and register it in
`src/ui/vanilla.ts`, add its type declaration if needed, and style it in
`components.css`. Do not import the entire preset: the published preset's
unrelated dialog/tab imports are incompatible with its current core package.

The installed components replace their custom tags with ordinary HTML elements.
Query controls after registration, keep your classes on the custom tags, and
attach dynamic button handlers to a stable parent using event delegation.
The switch adapter forwards `change` from the visible button because version
0.4.3 otherwise dispatches it on the detached custom element.

MapLibre still owns the canvas, scale, attribution, and popup positioning.
Its interactive navigation and popup close actions use Vanilla UI buttons;
native scale/attribution are themed in `map.css` and remain functional.

## Run and build

From `frontend/`, run `npm run dev` or `npm run build`. Both commands first
convert `../backend/data/intersections.csv` into `public/data/intersections.geojson`
using Python 3's standard library. Run the ingestion cleaner first if the CSV is missing.
After changing the CSV, restart the development server or run `npm run export:data`
and refresh the browser. Production updates require a new build.

The generated GeoJSON is ignored in Git and included in the production build.
The frontend fetches it from the same origin; an API/database is not required for
this overlay. A future intersection API can replace this URL if it returns GeoJSON.

The map uses one source for two layers: a crash-count-weighted heatmap and
clickable circles. The heatmap fades as the circles appear at closer zoom levels.
Turning heat off makes the circles visible at every allowed zoom. Both layers
can be toggled independently. They are placed below base-map labels.

Heat weights use square-root crash counts normalized by the highest count,
so high-count intersections contribute more without overwhelming smaller ones.
Heat colors describe relative smoothed concentration and vary with zoom, not
absolute counts or crash probability. Circle sizes/colors increase with total
crashes; popups provide exact counts and the years represented by each summary.
Counts exclude review records and are not annualized. Shared coordinates remain
separate features, so dots can overlap; their popups identify this limitation.

Only cleaned summary properties are exported, not the full crash-record CSV or
backend environment variables. Database IDs can be added when the API is connected.

## Verification

Run `npm run build` for TypeScript checking and a production build. After starting
`npm run dev`, check both layer switches with mouse and Space/Enter, the navigation
buttons, popup closing, and the mobile layout. Full browser checks have not been
run for this change; component-level switch behavior was checked separately.
