import './style.css';
import { MapLibreMapComponent } from './mapLibre';

new MapLibreMapComponent({
  target: '#map',
  center: [-123.1207, 49.2827],
  zoom: 11,
  pitch: 0,
  bearing: 0,
});