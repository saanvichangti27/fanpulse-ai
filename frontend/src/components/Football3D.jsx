import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, Icosahedron, Sphere } from "@react-three/drei";
import { Suspense, useMemo, useRef } from "react";
import * as THREE from "three";

function Football() {
  const group = useRef(null);
  useFrame((state, dt) => {
    if (!group.current) return;
    group.current.rotation.y += dt * 0.35;
    group.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.4) * 0.18;
  });

  // Position hex/pentagon dots on an icosahedron for a football-panel look
  const points = useMemo(() => {
    const geom = new THREE.IcosahedronGeometry(1.02, 1);
    const pos = geom.attributes.position;
    const list = [];
    const seen = new Set();
    for (let i = 0; i < pos.count; i++) {
      const v = new THREE.Vector3().fromBufferAttribute(pos, i).normalize().multiplyScalar(1.02);
      const key = `${v.x.toFixed(2)}|${v.y.toFixed(2)}|${v.z.toFixed(2)}`;
      if (!seen.has(key)) {
        seen.add(key);
        list.push(v);
      }
    }
    return list;
  }, []);

  return (
    <group ref={group}>
      {/* Core dark ball */}
      <Sphere args={[1, 96, 96]}>
        <meshStandardMaterial color="#0b1226" metalness={0.85} roughness={0.28} envMapIntensity={0.85} />
      </Sphere>

      {/* Chrome panel accents */}
      {points.map((p, i) => (
        <mesh key={i} position={p.toArray()}>
          <Icosahedron args={[0.075, 0]}>
            <meshStandardMaterial
              color="#f1f5f9"
              metalness={1}
              roughness={0.15}
              emissive="#e2e8f0"
              emissiveIntensity={0.08}
            />
          </Icosahedron>
        </mesh>
      ))}

      {/* Faint outer wireframe halo */}
      <mesh>
        <icosahedronGeometry args={[1.28, 1]} />
        <meshBasicMaterial color="#e2e8f0" wireframe transparent opacity={0.06} />
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
        {/* Rim + key lighting */}
        <ambientLight intensity={0.15} />
        <directionalLight position={[5, 4, 3]} intensity={1.4} color="#ffffff" />
        <directionalLight position={[-4, -1, -3]} intensity={1.1} color="#8fb4ff" />
        <pointLight position={[0, -3, 2]} intensity={0.4} color="#e2e8f0" />

        <Suspense fallback={null}>
          <Football />
          <Environment preset="studio" />
        </Suspense>
      </Canvas>
    </div>
  );
}
