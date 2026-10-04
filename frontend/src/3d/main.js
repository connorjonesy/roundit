// main.js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { createRoundabout } from './roundabout.js';

const container = document.getElementById('roundabout');
const scene = new THREE.Scene();
//scene.background = new THREE.Color(0xbfd8ee);

const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 500);
camera.position.set(35, 30, 35);


const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setClearColor(0x000000, 0); // fully transparent clear color
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const sun = new THREE.DirectionalLight(0xffffff, 1.2);
sun.position.set(20, 40, 10);
scene.add(sun);

const roundabout = createRoundabout({ arms: 4 });
scene.add(roundabout);

const controls = new OrbitControls(camera, renderer.domElement);
controls.maxPolarAngle = Math.PI / 2.1; // don't go below the ground

const clock = new THREE.Clock();

renderer.setAnimationLoop(() => {
	const dt = clock.getDelta();            // seconds since the last frame
	roundabout.rotation.y += dt * 0.5;      // radians per second
	controls.update();
	renderer.render(scene, camera);
});

new ResizeObserver(() => {
	camera.aspect = container.clientWidth / container.clientHeight;
	camera.updateProjectionMatrix();
	renderer.setSize(container.clientWidth, container.clientHeight);
}).observe(container);
