// roundabout.js
import * as THREE from 'three';

const trunkMat = new THREE.MeshStandardMaterial({ color: 0x6b4423, roughness: 1 });
const leafMat = new THREE.MeshStandardMaterial({ color: 0x2f6b2f, roughness: 0.9 });

function createTree(scale = 1) {
	const tree = new THREE.Group();

	const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.25, 1.6, 8), trunkMat);
	trunk.position.y = 0.8;

	const lowerLeaves = new THREE.Mesh(new THREE.ConeGeometry(1.2, 2.2, 8), leafMat);
	lowerLeaves.position.y = 2.4;

	const upperLeaves = new THREE.Mesh(new THREE.ConeGeometry(0.9, 1.8, 8), leafMat);
	upperLeaves.position.y = 3.5;

	[trunk, lowerLeaves, upperLeaves].forEach((m) => (m.castShadow = true));
	tree.add(trunk, lowerLeaves, upperLeaves);
	tree.scale.setScalar(scale);
	return tree;
}

export function createRoundabout({ islandR = 6, laneW = 6, arms = 4, armLen = 10, armW = 7 } = {}) {
	const group = new THREE.Group();
	const asphalt = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.9 });
	const yellow_paint = new THREE.MeshStandardMaterial({ color: 0xfcba03 });
	const white_paint = new THREE.MeshStandardMaterial({ color: 0xffffff });
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
		const dash = new THREE.Mesh(new THREE.PlaneGeometry(1, 0.15), white_paint);
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

		const line = new THREE.Mesh(new THREE.PlaneGeometry(armLen, 0.15), yellow_paint);
		line.rotation.x = -Math.PI / 2;
		line.position.set(outerR + armLen / 2 - 0.5, 0.02, 0);

		pivot.add(road, line);
		group.add(pivot);
	}
	// Trees on the central island (island top is at y = 0.4)
	const treeSpots = [
		{ x: 0, z: 0, s: 1.3 },
		{ x: islandR * 0.55, z: islandR * 0.1, s: 0.9 },
		{ x: -islandR * 0.4, z: islandR * 0.45, s: 1.0 },
		{ x: -islandR * 0.25, z: -islandR * 0.55, s: 0.8 },
	];

	treeSpots.forEach(({ x, z, s }) => {
		const tree = createTree(s);
		tree.position.set(x, 0.4, z);
		group.add(tree);
	});

	return group;
}
