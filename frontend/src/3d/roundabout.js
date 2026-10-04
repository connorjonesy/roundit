// roundabout.js
import * as THREE from 'three';

export function createRoundabout({ islandR = 6, laneW = 6, arms = 4, armLen = 30, armW = 7 } = {}) {
	const group = new THREE.Group();
	const asphalt = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.9 });
	const paint = new THREE.MeshStandardMaterial({ color: 0xffffff });
	const grass = new THREE.MeshStandardMaterial({ color: 0x4a7c3a });
	const outerR = islandR + laneW;

	// Circulating lane
	const ring = new THREE.Mesh(new THREE.RingGeometry(islandR, outerR, 64), asphalt);
	ring.rotation.x = -Math.PI / 2;
	group.add(ring);

	// Central island
	const island = new THREE.Mesh(new THREE.CylinderGeometry(islandR, islandR, 0.4, 48), grass);
	island.position.y = 0.2;
	group.add(island);

	// Dashed lane marking on the ring
	const midR = islandR + laneW / 2;
	for (let i = 0; i < 48; i += 2) {
		const a = (i / 48) * Math.PI * 2;
		const dash = new THREE.Mesh(new THREE.PlaneGeometry(1, 0.15), paint);
		dash.rotation.x = -Math.PI / 2;
		dash.rotation.z = a + Math.PI / 2;
		dash.position.set(Math.cos(a) * midR, 0.02, -Math.sin(a) * midR);
		group.add(dash);
	}

	// Approach roads, each with a centre line
	for (let i = 0; i < arms; i++) {
		const pivot = new THREE.Group();
		pivot.rotation.y = (i / arms) * Math.PI * 2;

		const road = new THREE.Mesh(new THREE.PlaneGeometry(armLen, armW), asphalt);
		road.rotation.x = -Math.PI / 2;
		road.position.set(outerR + armLen / 2 - 0.5, 0.01, 0);

		const line = new THREE.Mesh(new THREE.PlaneGeometry(armLen, 0.15), paint);
		line.rotation.x = -Math.PI / 2;
		line.position.set(outerR + armLen / 2 - 0.5, 0.02, 0);

		pivot.add(road, line);
		group.add(pivot);
	}
	return group;
}
