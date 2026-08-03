import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Sphere, MeshDistortMaterial, Torus } from '@react-three/drei'
import * as THREE from 'three'

// The pulsing inner core
function InnerCore() {
  const meshRef = useRef<THREE.Mesh>(null)
  
  useFrame((state) => {
    if (meshRef.current) {
      const time = state.clock.getElapsedTime()
      // Pulse scale
      const scale = 0.8 + Math.sin(time * 3) * 0.05
      meshRef.current.scale.set(scale, scale, scale)
      // Rotate slowly
      meshRef.current.rotation.y = time * 0.8
      meshRef.current.rotation.x = time * 0.4
    }
  })

  return (
    <Sphere ref={meshRef} args={[1, 32, 32]}>
      <meshStandardMaterial 
        color="#00f3ff" 
        emissive="#00f3ff" 
        emissiveIntensity={1.5} 
        wireframe={true} 
        transparent 
        opacity={0.8}
      />
    </Sphere>
  )
}

// Concentric rotating rings (Segments)
function OrbitalRings() {
  const ringsRef = useRef<THREE.Group>(null)
  
  useFrame((state) => {
    if (ringsRef.current) {
      const time = state.clock.getElapsedTime()
      ringsRef.current.children.forEach((ring, i) => {
        // Different rotation speeds and axes per ring
        ring.rotation.x = time * (0.15 + i * 0.1)
        ring.rotation.y = time * (0.2 - i * 0.05)
      })
    }
  })

  return (
    <group ref={ringsRef}>
      {[...Array(5)].map((_, i) => (
        <Torus key={i} args={[1.5 + i * 0.4, 0.005, 16, 100]} rotation={[Math.random() * Math.PI, Math.random() * Math.PI, 0]}>
          <meshBasicMaterial color="#00aaff" transparent opacity={0.3 + (i * 0.1)} />
        </Torus>
      ))}
    </group>
  )
}

// Lights coming in and going out (Data Streams)
function DataStreams() {
  const count = 300
  const mesh = useRef<THREE.InstancedMesh>(null)
  
  const dummy = new THREE.Object3D()
  const color = new THREE.Color()
  
  // Store initial positions and speeds
  const particleData = useMemo(() => {
    const data = []
    for(let i=0; i<count; i++) {
      // Random direction vector
      const vec = new THREE.Vector3(
        (Math.random() - 0.5) * 2,
        (Math.random() - 0.5) * 2,
        (Math.random() - 0.5) * 2
      ).normalize()
      
      data.push({
        dir: vec,
        distance: Math.random() * 6 + 1, // Start distance between 1 and 7
        speed: (Math.random() * 3 + 1) * (Math.random() > 0.5 ? 1 : -1), // In or out
        baseSize: Math.random() * 0.04 + 0.01
      })
    }
    return data
  }, [count])

  useFrame((state) => {
    if (!mesh.current) return
    const time = state.clock.getElapsedTime()
    
    for (let i = 0; i < count; i++) {
      const pd = particleData[i]
      
      // Update distance based on speed and time
      // Loop between radius 1 and 7
      let currentDist = pd.distance + time * pd.speed
      currentDist = ((currentDist - 1) % 6 + 6) % 6 + 1
      
      dummy.position.copy(pd.dir).multiplyScalar(currentDist)
      
      // Scale based on distance (closer = smaller/fade)
      const scale = pd.baseSize * (currentDist / 7)
      dummy.scale.set(scale, scale, scale)
      
      dummy.updateMatrix()
      mesh.current.setMatrixAt(i, dummy.matrix)
      
      // Set color intensity based on direction and position
      const intensity = pd.speed > 0 ? (currentDist/7) : (1 - currentDist/7)
      color.set("#00f3ff").multiplyScalar(intensity + 0.1)
      mesh.current.setColorAt(i, color)
    }
    mesh.current.instanceMatrix.needsUpdate = true
    if (mesh.current.instanceColor) mesh.current.instanceColor.needsUpdate = true
    mesh.current.rotation.y = time * 0.05
    mesh.current.rotation.z = time * 0.02
  })

  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, count]}>
      <sphereGeometry args={[1, 8, 8]} />
      <meshBasicMaterial transparent opacity={0.9} />
    </instancedMesh>
  )
}

function HologramShell() {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.getElapsedTime() * 0.1
      meshRef.current.rotation.z = state.clock.getElapsedTime() * 0.05
    }
  })

  return (
    <Sphere ref={meshRef} args={[2.8, 48, 48]}>
      <MeshDistortMaterial
        color="#0066ff"
        attach="material"
        distort={0.15}
        speed={1.5}
        roughness={0.2}
        metalness={0.9}
        emissive="#0033ff"
        emissiveIntensity={0.2}
        wireframe={true}
        transparent
        opacity={0.08}
      />
    </Sphere>
  )
}

export default function AICore() {
  return (
    <div className="w-full h-full absolute inset-0 flex items-center justify-center pointer-events-none">
      {/* Outer decorative rings (scaled up for full screen effect) */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] border border-void-cyan/5 rounded-full animate-[spin_60s_linear_infinite] border-t-void-cyan/20" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] border border-void-blue/10 rounded-full animate-[spin_40s_linear_infinite_reverse] border-b-void-blue/30" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[450px] h-[450px] border border-void-cyan/10 rounded-full animate-[spin_20s_linear_infinite] border-l-void-cyan/40 border-r-void-cyan/10" />
      
      <div className="absolute inset-0 z-10 pointer-events-auto">
        <Canvas camera={{ position: [0, 0, 9], fov: 45 }}>
          <ambientLight intensity={0.2} />
          <pointLight position={[10, 10, 10]} intensity={1.5} color="#00f3ff" />
          <pointLight position={[-10, -10, -10]} intensity={0.5} color="#0066ff" />
          
          <InnerCore />
          <OrbitalRings />
          <DataStreams />
          <HologramShell />
        </Canvas>
      </div>
      
      {/* Center Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-void-cyan/10 rounded-full blur-[120px]" />
    </div>
  )
}
