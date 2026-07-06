import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, ContactShadows } from "@react-three/drei";
import { Suspense, useEffect, useMemo, useRef } from "react";
import * as THREE from "three";

function Pentagon({ position, radius }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current) return;
    const p = new THREE.Vector3(...position).multiplyScalar(2);
    ref.current.lookAt(p);
  }, [position]);
  return (
    <group ref={ref} position={position}>
      {/* Panel */}
      <mesh>
        <circleGeometry args={[radius, 5]} />
        <meshStandardMaterial
          color="#0b1220"
          roughness={0.65}
          metalness={0.15}
        />
      </mesh>
      {/* Subtle stitch ring */}
      <mesh position={[0, 0, 0.001]}>
        <ringGeometry args={[radius * 0.94, radius * 0.99, 5]} />
        <meshBasicMaterial color="#1e293b" transparent opacity={0.55} />
      </mesh>
    </group>
  );
}

function HexHint({ position }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current) return;
    const p = new THREE.Vector3(...position).multiplyScalar(2);
    ref.current.lookAt(p);
  }, [position]);
  return (
    <mesh ref={ref} position={position}>
      {/* 6-sided flat panel with faint grey wash */}
      <circleGeometry args={[0.19, 6]} />
      <meshBasicMaterial color="#e2e8f0" transparent opacity={0.06} />
    </mesh>
  );
}

function Ball() {
  const group = useRef(null);
  useFrame((state, dt) => {
    if (!group.current) return;
    group.current.rotation.y += dt * 0.22;
    group.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
  });

  // 12 icosahedron vertices → pentagon centers
  const pentagonPositions = useMemo(() => {
    const g = new THREE.IcosahedronGeometry(1, 0);
    const pos = g.attributes.position;
    const seen = new Map();
    for (let i = 0; i < pos.count; i++) {
      const v = new THREE.Vector3().fromBufferAttribute(pos, i).normalize();
      const key = `${v.x.toFixed(3)}|${v.y.toFixed(3)}|${v.z.toFixed(3)}`;
      if (!seen.has(key)) seen.set(key, v.clone().multiplyScalar(1.005));
    }
    return Array.from(seen.values()).map((v) => v.toArray());
  }, []);

  // 20 face centers → hexagon hint positions
  const hexPositions = useMemo(() => {
    const g = new THREE.IcosahedronGeometry(1, 0);
    const pos = g.attributes.position;
    const list = [];
    for (let i = 0; i < pos.count; i += 3) {
      const a = new THREE.Vector3().fromBufferAttribute(pos, i);
      const b = new THREE.Vector3().fromBufferAttribute(pos, i + 1);
      const c = new THREE.Vector3().fromBufferAttribute(pos, i + 2);
      const centre = a.add(b).add(c).divideScalar(3).normalize().multiplyScalar(1.004);
      list.push(centre.toArray());
    }
    return list;
  }, []);

  return (
    <group ref={group}>
      {/* Base sphere — warm off-white, subtle sheen */}
      <mesh castShadow>
        <sphereGeometry args={[1, 128, 128]} />
        <meshStandardMaterial
          color="#f5f5f4"
          roughness={0.42}
          metalness={0.08}
          envMapIntensity={0.6}
        />
      </mesh>

      {/* 12 dark pentagon panels */}
      {pentagonPositions.map((p, i) => (
        <Pentagon key={`p-${i}`} position={p} radius={0.3} />
      ))}

      {/* 20 subtle hexagon hints (grey wash) */}
      {hexPositions.map((p, i) => (
        <HexHint key={`h-${i}`} position={p} />
      ))}
    </group>
  );
}

export default function Football3D() {
  return (
    <div className="relative w-full h-full" data-testid="hero-3d-football">
      <Canvas
        shadows
        camera={{ position: [0, 0.15, 3.4], fov: 40 }}
        dpr={[1, 1.8]}
        gl={{ antialias: true, alpha: true }}
      >
        {/* Softer, film-like key + rim */}
        <ambientLight intensity={0.35} />
        <directionalLight
          position={[4, 5, 3]}
          intensity={1.3}
          color="#fffdf5"
          castShadow
          shadow-mapSize={[1024, 1024]}
        />
        <directionalLight position={[-4, 1, -3]} intensity={0.55} color="#a3e635" />
        <pointLight position={[0, -3, 2]} intensity={0.35} color="#3b82f6" />

        <Suspense fallback={null}>
          <Ball />
          <ContactShadows
            position={[0, -1.05, 0]}
            opacity={0.45}
            scale={5}
            blur={2.4}
            far={2}
            color="#000000"
          />
          <Environment preset="apartment" />
        </Suspense>
      </Canvas>
    </div>
  );
}
