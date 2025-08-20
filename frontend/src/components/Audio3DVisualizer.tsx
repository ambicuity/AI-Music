import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface Audio3DVisualizerProps {
  audioData?: {
    frequencyData: number[];
    amplitudeData: number[];
    beatData: any[];
  };
  width?: number;
  height?: number;
  visualizationType?: 'wave3d' | 'particles' | 'sphere' | 'tunnel';
}

const Audio3DVisualizer: React.FC<Audio3DVisualizerProps> = ({
  audioData,
  width = 800,
  height = 600,
  visualizationType = 'wave3d'
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const cameraRef = useRef<THREE.PerspectiveCamera>();
  const animationRef = useRef<number>();
  const geometryRef = useRef<THREE.BufferGeometry>();
  const materialRef = useRef<THREE.Material>();
  const meshRef = useRef<THREE.Mesh>();

  useEffect(() => {
    if (!mountRef.current) return;

    // Initialize Three.js scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000011);
    sceneRef.current = scene;

    // Initialize camera
    const camera = new THREE.PerspectiveCamera(
      75,
      width / height,
      0.1,
      1000
    );
    camera.position.z = 5;
    cameraRef.current = camera;

    // Initialize renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setClearColor(0x000011);
    rendererRef.current = renderer;

    // Add renderer to DOM
    mountRef.current.appendChild(renderer.domElement);

    // Add lights
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0xffffff, 1, 100);
    pointLight.position.set(10, 10, 10);
    scene.add(pointLight);

    // Initialize visualization based on type
    initializeVisualization();

    // Start animation loop
    animate();

    // Cleanup function
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (rendererRef.current && mountRef.current) {
        mountRef.current.removeChild(rendererRef.current.domElement);
        rendererRef.current.dispose();
      }
    };
  }, [width, height, visualizationType]);

  useEffect(() => {
    // Update visualization when audio data changes
    if (audioData) {
      updateVisualization();
    }
  }, [audioData]);

  const initializeVisualization = () => {
    if (!sceneRef.current) return;

    // Clear existing mesh
    if (meshRef.current) {
      sceneRef.current.remove(meshRef.current);
    }

    switch (visualizationType) {
      case 'wave3d':
        initWave3D();
        break;
      case 'particles':
        initParticles();
        break;
      case 'sphere':
        initSphere();
        break;
      case 'tunnel':
        initTunnel();
        break;
    }
  };

  const initWave3D = () => {
    const segments = 128;
    const geometry = new THREE.PlaneGeometry(8, 8, segments - 1, segments - 1);
    
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        audioData: { value: new Float32Array(segments) },
        colorMultiplier: { value: 1.0 }
      },
      vertexShader: `
        uniform float time;
        uniform float audioData[128];
        varying vec3 vPosition;
        varying vec3 vNormal;
        
        void main() {
          vPosition = position;
          vNormal = normal;
          
          vec3 pos = position;
          int index = int(floor((position.x + 4.0) / 8.0 * 127.0));
          index = clamp(index, 0, 127);
          
          float wave = audioData[index] * 0.01;
          pos.z += wave + sin(time * 2.0 + position.x * 2.0) * 0.1;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform float colorMultiplier;
        varying vec3 vPosition;
        varying vec3 vNormal;
        
        void main() {
          float intensity = length(vNormal);
          vec3 color = vec3(
            0.5 + 0.5 * sin(time + vPosition.x * 2.0),
            0.5 + 0.5 * sin(time + vPosition.y * 2.0 + 1.0),
            0.5 + 0.5 * sin(time + vPosition.z * 2.0 + 2.0)
          ) * colorMultiplier;
          
          gl_FragColor = vec4(color * intensity, 1.0);
        }
      `,
      wireframe: true
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.x = -Math.PI / 3;
    
    geometryRef.current = geometry;
    materialRef.current = material;
    meshRef.current = mesh;
    sceneRef.current!.add(mesh);
  };

  const initParticles = () => {
    const particleCount = 2000;
    const geometry = new THREE.BufferGeometry();
    
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      positions[i3] = (Math.random() - 0.5) * 20;
      positions[i3 + 1] = (Math.random() - 0.5) * 20;
      positions[i3 + 2] = (Math.random() - 0.5) * 20;
      
      colors[i3] = Math.random();
      colors[i3 + 1] = Math.random();
      colors[i3 + 2] = Math.random();
      
      sizes[i] = Math.random() * 4 + 1;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        audioIntensity: { value: 0 }
      },
      vertexShader: `
        attribute float size;
        uniform float time;
        uniform float audioIntensity;
        varying vec3 vColor;
        
        void main() {
          vColor = color;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          
          float audioEffect = audioIntensity * 0.1;
          gl_PointSize = size * (1.0 + audioEffect) * (300.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        
        void main() {
          float r = length(gl_PointCoord - vec2(0.5, 0.5));
          if (r > 0.5) discard;
          
          float intensity = 1.0 - r * 2.0;
          gl_FragColor = vec4(vColor * intensity, intensity);
        }
      `,
      transparent: true,
      vertexColors: true
    });

    const points = new THREE.Points(geometry, material);
    
    geometryRef.current = geometry;
    materialRef.current = material;
    meshRef.current = points as any;
    sceneRef.current!.add(points);
  };

  const initSphere = () => {
    const geometry = new THREE.SphereGeometry(2, 64, 64);
    
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        audioData: { value: new Float32Array(64) }
      },
      vertexShader: `
        uniform float time;
        uniform float audioData[64];
        varying vec3 vPosition;
        varying vec3 vNormal;
        
        void main() {
          vPosition = position;
          vNormal = normal;
          
          vec3 pos = position;
          
          // Map position to audio data index
          float theta = atan(pos.z, pos.x) + 3.14159;
          float phi = acos(pos.y / length(pos));
          int index = int(floor(theta / 6.28318 * 63.0));
          index = clamp(index, 0, 63);
          
          float displacement = audioData[index] * 0.01;
          pos += normalize(pos) * displacement;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        varying vec3 vPosition;
        varying vec3 vNormal;
        
        void main() {
          vec3 color = vec3(
            0.5 + 0.5 * sin(time + vPosition.x * 3.0),
            0.5 + 0.5 * sin(time + vPosition.y * 3.0 + 2.0),
            0.5 + 0.5 * sin(time + vPosition.z * 3.0 + 4.0)
          );
          
          float intensity = dot(vNormal, normalize(vec3(1, 1, 1)));
          gl_FragColor = vec4(color * intensity, 1.0);
        }
      `,
      wireframe: false
    });

    const mesh = new THREE.Mesh(geometry, material);
    
    geometryRef.current = geometry;
    materialRef.current = material;
    meshRef.current = mesh;
    sceneRef.current!.add(mesh);
  };

  const initTunnel = () => {
    const geometry = new THREE.CylinderGeometry(3, 3, 10, 32, 50, true);
    
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        audioIntensity: { value: 0 }
      },
      vertexShader: `
        uniform float time;
        uniform float audioIntensity;
        varying vec2 vUv;
        varying vec3 vPosition;
        
        void main() {
          vUv = uv;
          vPosition = position;
          
          vec3 pos = position;
          float wave = sin(time * 2.0 + pos.y * 0.5) * audioIntensity * 0.1;
          pos.x += wave;
          pos.z += wave;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform float audioIntensity;
        varying vec2 vUv;
        varying vec3 vPosition;
        
        void main() {
          float intensity = audioIntensity * 0.5 + 0.3;
          vec3 color = vec3(
            0.5 + 0.5 * sin(time + vUv.x * 10.0),
            0.3 + 0.3 * sin(time + vUv.y * 8.0 + 1.0),
            0.8 + 0.2 * sin(time + (vUv.x + vUv.y) * 6.0 + 2.0)
          ) * intensity;
          
          float alpha = 1.0 - abs(vPosition.y / 5.0);
          gl_FragColor = vec4(color, alpha * 0.8);
        }
      `,
      transparent: true,
      side: THREE.DoubleSide
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.x = Math.PI / 2;
    
    geometryRef.current = geometry;
    materialRef.current = material;
    meshRef.current = mesh;
    sceneRef.current!.add(mesh);
  };

  const updateVisualization = () => {
    if (!audioData || !materialRef.current) return;

    const material = materialRef.current as THREE.ShaderMaterial;
    
    if (material.uniforms) {
      // Update audio data in shaders
      if (material.uniforms.audioData) {
        const audioArray = new Float32Array(128);
        for (let i = 0; i < Math.min(128, audioData.frequencyData.length); i++) {
          audioArray[i] = audioData.frequencyData[i];
        }
        material.uniforms.audioData.value = audioArray;
      }

      // Update audio intensity
      if (material.uniforms.audioIntensity) {
        const intensity = audioData.frequencyData.reduce((sum, val) => sum + val, 0) / audioData.frequencyData.length;
        material.uniforms.audioIntensity.value = intensity / 255;
      }

      // Update color multiplier
      if (material.uniforms.colorMultiplier) {
        const intensity = audioData.frequencyData.reduce((sum, val) => sum + val, 0) / audioData.frequencyData.length;
        material.uniforms.colorMultiplier.value = 0.5 + (intensity / 255) * 1.5;
      }
    }
  };

  const animate = () => {
    animationRef.current = requestAnimationFrame(animate);

    if (!sceneRef.current || !cameraRef.current || !rendererRef.current) return;

    const time = Date.now() * 0.001;

    // Update material uniforms
    if (materialRef.current && (materialRef.current as THREE.ShaderMaterial).uniforms) {
      const material = materialRef.current as THREE.ShaderMaterial;
      if (material.uniforms.time) {
        material.uniforms.time.value = time;
      }
    }

    // Rotate camera around the scene
    if (visualizationType === 'tunnel') {
      cameraRef.current.position.z = 3 + Math.sin(time * 0.5) * 2;
    } else if (visualizationType === 'sphere' || visualizationType === 'particles') {
      cameraRef.current.position.x = Math.cos(time * 0.3) * 8;
      cameraRef.current.position.z = Math.sin(time * 0.3) * 8;
      cameraRef.current.lookAt(0, 0, 0);
    }

    // Render the scene
    rendererRef.current.render(sceneRef.current, cameraRef.current);
  };

  return (
    <div className="audio-3d-visualizer">
      <div className="visualizer-controls">
        <h3>3D Audio Visualizer</h3>
        <p>Type: {visualizationType}</p>
      </div>
      <div ref={mountRef} className="three-container" />
      
      <style jsx>{`
        .audio-3d-visualizer {
          background: #0a0a0a;
          border-radius: 12px;
          padding: 20px;
          margin: 20px 0;
        }
        
        .visualizer-controls {
          margin-bottom: 15px;
          color: #fff;
        }
        
        .visualizer-controls h3 {
          margin: 0 0 5px 0;
          color: #4a9eff;
        }
        
        .visualizer-controls p {
          margin: 0;
          color: #ccc;
          text-transform: capitalize;
        }
        
        .three-container {
          width: 100%;
          height: ${height}px;
          border-radius: 8px;
          overflow: hidden;
        }
        
        .three-container canvas {
          display: block;
          width: 100% !important;
          height: 100% !important;
        }
      `}</style>
    </div>
  );
};

export default Audio3DVisualizer;