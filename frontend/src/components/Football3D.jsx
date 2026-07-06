import { Canvas, useFrame } from "@react-three/fiber";
import { Environment } from "@react-three/drei";
import { Suspense, useEffect, useMemo, useRef } from "react";
import * as THREE from "three";

function PentagonPatch({ position }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current) return;
    const p = new THREE.Vector3(...position).multiplyScalar(2);
    ref.current.lookAt(p);
  }, [position]);
  return (
    <mesh ref={ref} position={position}>
      <circleGeometry args={[0.34, 5]} />
      <meshStandardMaterial color="#0a0a0a" roughness={0.55} metalness={0.05} />
    </mesh>
  );
}

function Football() {
  const group = useRef(null);
  useFrame((state, dt) => {
    if (!group.current) return;
    group.current.rotation.y += dt * 0.28;
    group.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.35) * 0.14;
  });

  // 12 icosahedron vertices — these are the pentagon centres of a truncated icosahedron
  const patchPositions = useMemo(() => {
    const g = new THREE.IcosahedronGeometry(1, 0);
    const pos = g.attributes.position;
    const seen = new Map();
    for (let i = 0; i < pos.count; i++) {
      const v = new THREE.Vector3().fromBufferAttribute(pos, i).normalize();
      const key = `${v.x.toFixed(3)}|${v.y.toFixed(3)}|${v.z.toFixed(3)}`;
      if (!seen.has(key)) seen.set(key, v.clone().multiplyScalar(1.008));
    }
    return Array.from(seen.values()).map((v) => v.toArray());
  }, []);

  return (
    <group ref={group}>
      {/* White outer ball */}
      <mesh>
        <sphereGeometry args={[1, 96, 96]} />
        <meshStandardMaterial color="#f8fafc" roughness={0.35} metalness={0.05} />
      </mesh>

      {/* Black pentagon patches (12) */}
      {patchPositions.map((p, i) => (
        <PentagonPatch key={i} position={p} />
      ))}

      {/* Soft rim halo */}
      <mesh>
        <sphereGeometry args={[1.18, 48, 48]} />
        <meshBasicMaterial color="#a3e635" transparent opacity={0.05} side={THREE.BackSide} />
      </mesh>
    </group>
  );
}

export default function Football3D() {
  return (
    <div className="relative w-full h-full" data-testid="hero-3d-football">
      <Canvas
        camera={{ position: [0, 0, 3.4], fov: 42 }}
        dpr={[1, 1.6]}
        gl={{ antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.55} />
        <directionalLight position={[5, 4, 3]} intensity={1.6} color="#ffffff" />
        <directionalLight position={[-4, -1, -3]} intensity={0.8} color="#a3e635" />
        <pointLight position={[0, -3, 2]} intensity={0.5} color="#3b82f6" />

        <Suspense fallback={null}>
          <Football />
          <Environment preset="city" />
        </Suspense>
      </Canvas>
    </div>
  );
}
