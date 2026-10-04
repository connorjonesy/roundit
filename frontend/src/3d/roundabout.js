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
	const roadThickness = 2;
	const walkW = 2;     // sidewalk width
	const walkH = 0.15;  // how much the sidewalk rises above the road surface
	const walkMat = new THREE.MeshStandardMaterial({ color: 0xb8b8b8, roughness: 0.95 });
	const zebraLen = 3;        // crosswalk depth along the road direction
	const zebraStripeW = 0.5;  // width of each white stripe
	const zebraGap = 0.5;      // gap between stripes
	const zebraOffset = 3;     // distance from the ring's outer edge to the crosswalk center

	// Circulating lane as a thick slab
	const ringShape = new THREE.Shape();
	ringShape.absarc(0, 0, outerR, 0, Math.PI * 2, false);
	const hole = new THREE.Path();
	hole.absarc(0, 0, islandR, 0, Math.PI * 2, true);
	ringShape.holes.push(hole);

	const ring = new THREE.Mesh(
		new THREE.ExtrudeGeometry(ringShape, { depth: roadThickness, bevelEnabled: false, curveSegments: 64 }),
		asphalt
	);
	ring.rotation.x = -Math.PI / 2;
	ring.position.y = -roadThickness; // extrusion goes up from here, so the top lands at y = 0
	ring.receiveShadow = true;
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
	// Curved sidewalk around the ring, one segment between each pair of arms
	const halfAng = Math.asin(armW / 2 / outerR); // angular half-width of an arm at the ring
	for (let i = 0; i < arms; i++) {
		const a0 = (i / arms) * Math.PI * 2 + halfAng;
		const a1 = ((i + 1) / arms) * Math.PI * 2 - halfAng;
		if (a1 <= a0) continue; // too many arms for a gap to exist

		const shape = new THREE.Shape();
		shape.absarc(0, 0, outerR + walkW, a0, a1, false); // outer edge
		shape.absarc(0, 0, outerR, a1, a0, true);          // back along the inner edge
		shape.closePath();

		const walk = new THREE.Mesh(
			new THREE.ExtrudeGeometry(shape, { depth: roadThickness + walkH, bevelEnabled: false, curveSegments: 24 }),
			walkMat
		);
		walk.rotation.x = -Math.PI / 2;
		walk.position.y = -roadThickness; // bottom flush with the road slab, top at y = walkH
		walk.receiveShadow = true;
		group.add(walk);
	}

	// ARMS LOOP - Approach roads, each with a centre line
	for (let i = 0; i < arms; i++) {
		const pivot = new THREE.Group();
		pivot.rotation.y = (i / arms) * Math.PI * 2;

		const road = new THREE.Mesh(new THREE.BoxGeometry(armLen, roadThickness, armW), asphalt);
		road.position.set(outerR + armLen / 2 - 0.5, 0.01 - roadThickness / 2, 0);
		road.receiveShadow = true;

		// Sidewalk strips on both sides of this arm
		const stripStart = outerR * Math.cos(halfAng);
		const stripEnd = outerR + armLen - 0.5; // same end as the road
		const stripLen = stripEnd - stripStart;

		[-1, 1].forEach((side) => {
			const strip = new THREE.Mesh(
				new THREE.BoxGeometry(stripLen, roadThickness + walkH, walkW),
				walkMat
			);
			strip.position.set(
				(stripStart + stripEnd) / 2,
				(walkH - roadThickness) / 2,
				side * (armW / 2 + walkW / 2)
			);
			strip.receiveShadow = true;
			pivot.add(strip);
		});


		// Centre line: starts just past the crosswalk and runs to the end of the road
		const zebraX = outerR + zebraOffset;                  // crosswalk centre
		const lineGap = 0.6;
		const lineStart = zebraX + zebraLen / 2 + lineGap;
		const lineEnd = outerR + armLen - 0.5;                // same end as the road
		const lineLen = lineEnd - lineStart;

		const line = new THREE.Mesh(new THREE.PlaneGeometry(lineLen, 0.15), yellow_paint);
		line.rotation.x = -Math.PI / 2;
		line.position.set((lineStart + lineEnd) / 2, 0.02, 0);

		// Zebra crossing: stripes spaced across the arm's width
		const pitch = zebraStripeW + zebraGap;
		const margin = 0.6; // keep stripes off the road edges
		const count = Math.floor((armW - 2 * margin + zebraGap) / pitch);
		const span = count * pitch - zebraGap;      // total width actually covered

		for (let k = 0; k < count; k++) {
			const stripe = new THREE.Mesh(new THREE.PlaneGeometry(zebraLen, zebraStripeW), white_paint);
			stripe.rotation.x = -Math.PI / 2;
			stripe.position.set(
				zebraX,
				0.03, // above the centre line (0.02) so the stripes cover it
				-span / 2 + zebraStripeW / 2 + k * pitch
			);
			pivot.add(stripe);
		}

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
