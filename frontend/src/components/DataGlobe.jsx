import { Canvas, useFrame } from "@react-three/fiber";
import { Suspense, useMemo, useRef } from "react";
import * as THREE from "three";
import { COUNTRIES } from "@/data/mock";

const HOTSPOT_COLOR = {
  superfans: "#a3e635",
  traveling_ultras: "#ef4444",
  casual_streamers: "#38bdf8",
  deal_seekers: "#f59e0b",
  lapsed_fans: "#8b5cf6",
};

function latLngToVec3(lat, lng, r = 1) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta)
  );
}

function PointCloud() {
  const geom = useMemo(() => {
    const N = 900;
    const positions = new Float32Array(N * 3);
    const phi = Math.PI * (Math.sqrt(5) - 1);
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2;
      const r = Math.sqrt(1 - y * y);
      const theta = phi * i;
      const x = Math.cos(theta) * r;
      const z = Math.sin(theta) * r;
      positions[i * 3]     = x * 1.01;
      positions[i * 3 + 1] = y * 1.01;
      positions[i * 3 + 2] = z * 1.01;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return g;
  }, []);

  return (
    <points geometry={geom}>
      <pointsMaterial
        size={0.018}
        color="#ffffff"
        transparent
        opacity={0.62}
        sizeAttenuation
      />
    </points>
  );
}

function Hotspots({ nodes }) {
  return (
    <group>
      {nodes.map((n, i) => (
        <group key={i} position={n.pos.toArray()}>
          <mesh>
            <sphereGeometry args={[0.017, 12, 12]} />
            <meshBasicMaterial color={n.color} />
          </mesh>
          <mesh>
            <sphereGeometry args={[0.034, 16, 16]} />
            <meshBasicMaterial color={n.color} transparent opacity={0.22} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

function Arcs({ nodes }) {
  const arcs = useMemo(() => {
    // Deterministic pairings: connect largest 8 nodes in a loop for stability
    const top = [...nodes].sort((a, b) => b.weight - a.weight).slice(0, 10);
    const pairs = [];
    for (let i = 0; i < top.length; i++) {
      pairs.push([top[i], top[(i + 3) % top.length]]);
    }
    return pairs.map(([a, b]) => {
      const mid = a.pos.clone().add(b.pos).normalize().multiplyScalar(1.55);
      const curve = new THREE.QuadraticBezierCurve3(a.pos.clone().multiplyScalar(1.01), mid, b.pos.clone().multiplyScalar(1.01));
      return { curve, color: a.color };
    });
  }, [nodes]);

  return (
    <group>
      {arcs.map((a, i) => {
        const points = a.curve.getPoints(48);
        const g = new THREE.BufferGeometry().setFromPoints(points);
        return (
          <line key={i} geometry={g}>
            <lineBasicMaterial color={a.color} transparent opacity={0.55} />
          </line>
        );
      })}
    </group>
  );
}

function Globe() {
  const group = useRef(null);
  useFrame((_, dt) => {
    if (group.current) group.current.rotation.y += dt * 0.08;
  });

  const nodes = useMemo(
    () =>
      COUNTRIES.map((c) => ({
        pos: latLngToVec3(c.coords[1], c.coords[0], 1.02),
        color: HOTSPOT_COLOR[c.segment] || "#a3e635",
        weight: c.volume,
      })),
    []
  );

  return (
    <group ref={group}>
      {/* Solid inner sphere for silhouette */}
      <mesh>
        <sphereGeometry args={[1, 64, 64]} />
        <meshBasicMaterial color="#050914" />
      </mesh>
      {/* Wireframe overlay */}
      <mesh>
        <icosahedronGeometry args={[1.005, 4]} />
        <meshBasicMaterial color="#a3e635" wireframe transparent opacity={0.10} />
      </mesh>
      {/* Latitude rings */}
      {[-0.66, -0.33, 0, 0.33, 0.66].map((y, i) => {
        const r = Math.sqrt(1 - y * y) * 1.008;
        return (
          <mesh key={i} rotation={[Math.PI / 2, 0, 0]} position={[0, y, 0]}>
            <torusGeometry args={[r, 0.0015, 8, 96]} />
            <meshBasicMaterial color="#a3e635" transparent opacity={0.20} />
          </mesh>
        );
      })}
      {/* Longitude rings */}
      {Array.from({ length: 6 }).map((_, i) => {
        const rot = (i * Math.PI) / 6;
        return (
          <mesh key={i} rotation={[0, rot, 0]}>
            <torusGeometry args={[1.008, 0.0015, 8, 96]} />
            <meshBasicMaterial color="#a3e635" transparent opacity={0.10} />
          </mesh>
        );
      })}
      <PointCloud />
      <Hotspots nodes={nodes} />
      <Arcs nodes={nodes} />
      {/* Soft glowing atmosphere */}
      <mesh>
        <sphereGeometry args={[1.28, 48, 48]} />
        <meshBasicMaterial color="#a3e635" transparent opacity={0.05} side={THREE.BackSide} />
      </mesh>
    </group>
  );
}

export default function DataGlobe() {
  return (
    <div className="relative w-full h-full" data-testid="hero-data-globe">
      <Canvas
        camera={{ position: [0, 0.2, 3.1], fov: 42 }}
        dpr={[1, 1.6]}
        gl={{ antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.6} />
        <Suspense fallback={null}>
          <Globe />
        </Suspense>
      </Canvas>
    </div>
  );
}
