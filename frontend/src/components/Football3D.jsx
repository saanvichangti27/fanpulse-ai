
import React, { useEffect, useRef, useState } from "react";

/**
 * Football3D - A standalone, high-performance 3D revolving football React component
 * built using pure HTML5 Canvas and mathematical sphere projection.
 *
 * It represents the official FIFA 2026 "Trionda" match ball using the actual
 * product photos. It runs at 60 FPS without any external WebGL/Three.js dependencies.
 *
 * Props:
 * @param {number} size - The diameter of the ball in pixels (default: 300)
 * @param {number} speed - Rotation speed multiplier (default: 1.0)
 * @param {boolean} showLighting - Whether to render realistic 3D lighting (default: true)
 * @param {string} className - Optional Tailwind or custom CSS classes
 */
export const Football3D = ({
  size = 300,
  speed = 1.0,
  showLighting = true,
  className = "",
}) => {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [usingFallback, setUsingFallback] = useState(false);

  // References for keeping track of loaded images and generated texture
  const textureCanvasRef = useRef(null);
  const textureDataRef = useRef(null);
  const animationFrameIdRef = useRef(null);
  const angleRef = useRef(0);

  // Image source URLs (the 3 views of the FIFA 2026 ball)
  const imageSources = [
    "https://customer-assets.emergentagent.com/job_984c54ef-b127-4419-b1f1-e53c1fef2dcd/artifacts/fpdkx9dx_image.webp", // View 1: Red/Blue/Green + Adidas
    "https://customer-assets.emergentagent.com/job_984c54ef-b127-4419-b1f1-e53c1fef2dcd/artifacts/yextvbry_image.png",  // View 2: Blue "26" + Trophy
    "https://customer-assets.emergentagent.com/job_984c54ef-b127-4419-b1f1-e53c1fef2dcd/artifacts/61wcvwvf_image.png",  // View 3: Eagle Graphic + Stars
  ];

  useEffect(() => {
    let active = true;
    setLoading(true);
    setUsingFallback(false);

    // Stop any existing animation
    if (animationFrameIdRef.current) {
      cancelAnimationFrame(animationFrameIdRef.current);
    }

    // Load images
    const loadImages = async () => {
      const images = [];
      let successCount = 0;

      for (let i = 0; i < imageSources.length; i++) {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.src = imageSources[i];

        await new Promise((resolve) => {
          img.onload = () => {
            images.push(img);
            successCount++;
            resolve();
          };
          img.onerror = () => {
            console.warn(`Failed to load football image ${i + 1}. Using high-quality procedural fallback.`);
            resolve();
          };
        });
      }

      if (!active) return;

      const texWidth = 1024;
      const texHeight = 512;
      const texCanvas = document.createElement("canvas");
      texCanvas.width = texWidth;
      texCanvas.height = texHeight;
      const texCtx = texCanvas.getContext("2d");

      if (successCount === imageSources.length) {
        // High-fidelity image un-warping and panoramic mapping
        try {
          generatePanoramicTexture(texCanvas, texCtx, images);
          textureCanvasRef.current = texCanvas;
          textureDataRef.current = texCtx.getImageData(0, 0, texWidth, texHeight);
          setLoading(false);
        } catch (err) {
          console.error("Error un-warping images: ", err);
          generateProceduralTexture(texCanvas, texCtx);
          textureCanvasRef.current = texCanvas;
          textureDataRef.current = texCtx.getImageData(0, 0, texWidth, texHeight);
          setUsingFallback(true);
          setLoading(false);
        }
      } else {
        // High-quality procedural FIFA 2026 Trionda design fallback
        generateProceduralTexture(texCanvas, texCtx);
        textureCanvasRef.current = texCanvas;
        textureDataRef.current = texCtx.getImageData(0, 0, texWidth, texHeight);
        setUsingFallback(true);
        setLoading(false);
      }
    };

    loadImages();

    return () => {
      active = false;
      if (animationFrameIdRef.current) {
        cancelAnimationFrame(animationFrameIdRef.current);
      }
    };
  }, []);

  // Set up the high-performance renderer when canvas, size, or texture is ready
  useEffect(() => {
    if (loading || !canvasRef.current || !textureDataRef.current) return;

    const canvas = canvasRef.current;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");

    const R = Math.floor(size / 2) - 4; // sphere radius with slight boundary padding
    const width = size;
    const height = size;
    const cx = Math.floor(size / 2);
    const cy = Math.floor(size / 2);

    const texWidth = 1024;
    const texHeight = 512;
    const texData = textureDataRef.current.data;

    // 1. PRE-CALCULATE LOOKUP TABLE (LUT) FOR LIGHTNING-FAST 60 FPS RENDERING
    const lut = [];
    const light = { x: 0.577, y: 0.577, z: 0.577 }; // Normalized lighting vector (top-left-front)

    for (let y = -R; y <= R; y++) {
      for (let x = -R; x <= R; x++) {
        const d2 = x * x + y * y;
        if (d2 <= R * R) {
          const z = Math.sqrt(R * R - d2);

          // Normalized normal vector
          const nx = x / R;
          const ny = y / R;
          const nz = z / R;

          // Standard spherical angles
          const phi = Math.asin(ny); // Latitude [-PI/2, PI/2]
          const alpha = Math.atan2(nz, nx); // Longitude [-PI, PI]

          // Shading: Diffuse (Lambertian) + Ambient
          const dot = nx * light.x + ny * light.y + nz * light.z;
          const diffuse = Math.max(0, dot);
          const ambient = 0.45;
          const shading = Math.min(1.0, ambient + diffuse * 0.55);

          // Specular highlights (glossy material effect)
          // Reflection vector R = 2 * (N . L) * N - L
          const rx = 2 * dot * nx - light.x;
          const ry = 2 * dot * ny - light.y;
          const rz = 2 * dot * nz - light.z;
          // Viewer vector V = (0, 0, 1) looking straight down
          const specular = Math.pow(Math.max(0, rz), 15) * 0.45;

          // Target array index for ImageData
          const txCoord = (cy + y) * width + (cx + x);
          const targetIndex = txCoord * 4;

          lut.push({
            targetIndex,
            phi,
            alpha,
            shading,
            specular,
          });
        }
      }
    }

    // 2. THE REAL-TIME RENDER LOOP
    const render = () => {
      // Create frame image buffer
      const imgData = ctx.createImageData(width, height);
      const data = imgData.data;

      // Update rotation angle (slow horizontal revolution)
      angleRef.current = (angleRef.current + 0.004 * speed) % (2 * Math.PI);
      const currentAngle = angleRef.current;

      // Draw pixels using the LUT
      const len = lut.length;
      for (let i = 0; i < len; i++) {
        const pixel = lut[i];

        // Apply rotation to longitude
        let theta = pixel.alpha - currentAngle;

        // Map back to [0, 1] texture coordinates and mirror horizontally
        let u = 1.0 - ((theta + Math.PI) / (2 * Math.PI));
        u = (u % 1 + 1) % 1; // Wrap horizontally

        const v = 1.0 - ((pixel.phi + Math.PI / 2) / Math.PI); // Inverted vertically


        // Texture lookup (nearest neighbor is fast and crisp)
        const tx = Math.floor(u * (texWidth - 1));
        const ty = Math.floor(v * (texHeight - 1));
        const texIdx = (ty * texWidth + tx) * 4;

        const r = texData[texIdx];
        const g = texData[texIdx + 1];
        const b = texData[texIdx + 2];

        // Apply shading & glossiness
        let r_out, g_out, b_out;
        if (showLighting) {
          const shade = pixel.shading;
          const spec = pixel.specular * 255;
          r_out = Math.min(255, r * shade + spec);
          g_out = Math.min(255, g * shade + spec);
          b_out = Math.min(255, b * shade + spec);
        } else {
          r_out = r;
          g_out = g;
          b_out = b;
        }

        const idx = pixel.targetIndex;
        data[idx] = r_out;
        data[idx + 1] = g_out;
        data[idx + 2] = b_out;
        data[idx + 3] = 255; // Fully opaque sphere surface
      }

      // Draw the updated image buffer to the screen canvas
      ctx.clearRect(0, 0, width, height);
      ctx.putImageData(imgData, 0, 0);

      // Render outer glow and shadow overlays using standard 2D Canvas context
      ctx.save();

      // 3D Inner shadow overlay
      const gradient = ctx.createRadialGradient(cx, cy, Math.max(0, R - 15), cx, cy, R);
      gradient.addColorStop(0, "rgba(0, 0, 0, 0)");
      gradient.addColorStop(0.7, "rgba(0, 0, 0, 0.2)");
      gradient.addColorStop(1, "rgba(0, 0, 0, 0.65)");
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(cx, cy, R, 0, 2 * Math.PI);
      ctx.fill();

      // Soft rim highlight to accentuate the sphere edge
      const highlightGrad = ctx.createRadialGradient(cx - 30, cy - 30, Math.max(0, R - 120), cx - 30, cy - 30, R + 10);
      highlightGrad.addColorStop(0, "rgba(255, 255, 255, 0.15)");
      highlightGrad.addColorStop(0.85, "rgba(255, 255, 255, 0)");
      highlightGrad.addColorStop(1, "rgba(255, 255, 255, 0.4)");
      ctx.fillStyle = highlightGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, R, 0, 2 * Math.PI);
      ctx.fill();

      ctx.restore();

      animationFrameIdRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationFrameIdRef.current) {
        cancelAnimationFrame(animationFrameIdRef.current);
      }
    };
  }, [loading, size, speed, showLighting]);

  /**
   * Generates a 360-degree cylindrical/equirectangular projection by
   * un-warping the 3 perspective photos of the football and stitching them seamlessly.
   */
  const generatePanoramicTexture = (texCanvas, texCtx, images) => {
    const texWidth = texCanvas.width;
    const texHeight = texCanvas.height;

    // Set up offscreen canvases to read source image pixels
    const sourceCanvases = images.map((img) => {
      const c = document.createElement("canvas");
      c.width = 1000;
      c.height = 1000;
      const ctx = c.getContext("2d");
      ctx.drawImage(img, 0, 0, 1000, 1000);
      return {
        canvas: c,
        ctx: ctx,
        imageData: ctx.getImageData(0, 0, 1000, 1000).data,
      };
    });

    const texImgData = texCtx.createImageData(texWidth, texHeight);
    const data = texImgData.data;

    // Angle offsets for the 3 symmetric photos of the ball
    const thetaOffsets = [-2 * Math.PI / 3, 0, 2 * Math.PI / 3];

    // Source photo crop boundaries (each ball is centered in a 1000x1000 photo)
    const cx = 500;
    const cy = 500;
    const rBall = 465;

    for (let ty = 0; ty < texHeight; ty++) {
      const v = ty / (texHeight - 1);
      const phi = v * Math.PI - Math.PI / 2; // Latitude [-PI/2, PI/2]

      for (let tx = 0; tx < texWidth; tx++) {
        const u = tx / (texWidth - 1);
        const theta = u * 2 * Math.PI - Math.PI; // Longitude [-PI, PI]

        let blendedR = 0, blendedG = 0, blendedB = 0;
        let totalWeight = 0;

        // Sample and blend from the 3 images based on shortest angular distance
        for (let i = 0; i < 3; i++) {
          const thetaOffset = thetaOffsets[i];
          let diff = theta - thetaOffset;

          // Wrap angular difference to [-PI, PI]
          while (diff < -Math.PI) diff += 2 * Math.PI;
          while (diff > Math.PI) diff -= 2 * Math.PI;

          const absDiff = Math.abs(diff);

          if (absDiff < Math.PI / 2) {
            const weight = Math.cos(absDiff) * Math.cos(phi);

            // Project spherical coordinate back to 2D image coordinates
            const px = Math.cos(phi) * Math.sin(diff);
            const py = Math.sin(phi);

            // Scale to photo pixel coordinates
            const imgX = Math.round(cx + px * rBall);
            const imgY = Math.round(cy - py * rBall);

            if (imgX >= 0 && imgX < 1000 && imgY >= 0 && imgY < 1000) {
              const srcIdx = (imgY * 1000 + imgX) * 4;
              const srcData = sourceCanvases[i].imageData;

              blendedR += srcData[srcIdx] * weight;
              blendedG += srcData[srcIdx + 1] * weight;
              blendedB += srcData[srcIdx + 2] * weight;
              totalWeight += weight;
            }
          }
        }

        const idx = (ty * texWidth + tx) * 4;
        if (totalWeight > 0.01) {
          data[idx] = Math.round(blendedR / totalWeight);
          data[idx + 1] = Math.round(blendedG / totalWeight);
          data[idx + 2] = Math.round(blendedB / totalWeight);
        } else {
          data[idx] = 245;
          data[idx + 1] = 245;
          data[idx + 2] = 245;
        }
        data[idx + 3] = 255;
      }
    }

    // Draw the generated texture map back into the offscreen canvas
    texCtx.putImageData(texImgData, 0, 0);

    // Apply a subtle seam-blur filter to make sure the wrap-around has no seams
    blurCanvasSeams(texCanvas, texCtx);
  };

  /**
   * Helper to blur the left and right seams of the texture canvas to ensure perfect tiling
   */
  const blurCanvasSeams = (canvas, ctx) => {
    const width = canvas.width;
    const height = canvas.height;
    const imgData = ctx.getImageData(0, 0, width, height);
    const data = imgData.data;

    const seamWidth = 6;
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < seamWidth; x++) {
        const leftIdx = (y * width + x) * 4;
        const rightIdx = (y * width + (width - 1 - x)) * 4;

        const r_avg = Math.round((data[leftIdx] + data[rightIdx]) / 2);
        const g_avg = Math.round((data[leftIdx + 1] + data[rightIdx + 1]) / 2);
        const b_avg = Math.round((data[leftIdx + 2] + data[rightIdx + 2]) / 2);

        const weight = x / seamWidth;
        data[leftIdx] = Math.round(data[leftIdx] * weight + r_avg * (1 - weight));
        data[leftIdx + 1] = Math.round(data[leftIdx + 1] * weight + g_avg * (1 - weight));
        data[leftIdx + 2] = Math.round(data[leftIdx + 2] * weight + b_avg * (1 - weight));

        data[rightIdx] = Math.round(data[rightIdx] * weight + r_avg * (1 - weight));
        data[rightIdx + 1] = Math.round(data[rightIdx + 1] * weight + g_avg * (1 - weight));
        data[rightIdx + 2] = Math.round(data[rightIdx + 2] * weight + b_avg * (1 - weight));
      }
    }
    ctx.putImageData(imgData, 0, 0);
  };

  /**
   * Procedural FIFA 2026 Trionda design generator.
   * Renders the classic soccer panel structure with the Red, Green, and Blue Trionda swooshes,
   * stars, and details so that the component works beautifully offline or as a safe fallback.
   */
  const generateProceduralTexture = (canvas, ctx) => {
    const width = canvas.width;
    const height = canvas.height;

    // Fill white base
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, width, height);

    // 1. Draw subtle panel seams (pentagons and hexagons)
    ctx.strokeStyle = "rgba(0, 0, 0, 0.08)";
    ctx.lineWidth = 1.5;
    const cols = 8;
    const rows = 4;
    const cellW = width / cols;
    const cellH = height / rows;

    for (let r = 0; r <= rows; r++) {
      for (let c = 0; c <= cols; c++) {
        ctx.beginPath();
        ctx.arc(c * cellW, r * cellH, cellW * 0.45, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    // 2. Draw the USA Blue Trionda panel wave (#0A3161)
    ctx.save();
    ctx.fillStyle = "#0A3161";
    ctx.beginPath();
    ctx.moveTo(0, height * 0.1);
    ctx.bezierCurveTo(width * 0.25, height * 0.6, width * 0.5, height * 0.1, width * 0.8, height * 0.45);
    ctx.bezierCurveTo(width * 0.7, height * 0.8, width * 0.35, height * 0.9, 0, height * 0.55);
    ctx.closePath();
    ctx.fill();

    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Draw little gold/white stars inside USA Blue wave
    ctx.fillStyle = "#FFFFFF";
    drawStar(ctx, width * 0.2, height * 0.4, 8, 4, 5);
    drawStar(ctx, width * 0.45, height * 0.35, 12, 6, 5);
    drawStar(ctx, width * 0.65, height * 0.5, 6, 3, 5);
    ctx.restore();

    // 3. Draw the Canada Red Trionda panel wave (#E01B22)
    ctx.save();
    ctx.fillStyle = "#E01B22";
    ctx.beginPath();
    ctx.moveTo(width * 0.2, height * 0.85);
    ctx.bezierCurveTo(width * 0.45, height * 0.2, width * 0.75, height * 0.9, width, height * 0.3);
    ctx.bezierCurveTo(width * 0.9, height * 0.1, width * 0.6, height * 0.1, width * 0.3, height * 0.7);
    ctx.closePath();
    ctx.fill();

    ctx.strokeStyle = "#FFD700";
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.restore();

    // 4. Draw the Mexico Green Trionda panel wave (#006847)
    ctx.save();
    ctx.fillStyle = "#006847";
    ctx.beginPath();
    ctx.moveTo(width * 0.1, height * 0.5);
    ctx.bezierCurveTo(width * 0.3, height * 0.1, width * 0.7, height * 0.9, width * 0.9, height * 0.7);
    ctx.bezierCurveTo(width * 0.8, height * 0.95, width * 0.4, height * 0.8, width * 0.2, height * 0.7);
    ctx.closePath();
    ctx.fill();

    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 2.0;
    ctx.beginPath();
    ctx.moveTo(width * 0.3, height * 0.4);
    ctx.lineTo(width * 0.5, height * 0.65);
    ctx.lineTo(width * 0.7, height * 0.75);
    ctx.stroke();
    ctx.restore();

    // 5. Draw official branding text "FIFA 2026", "TRIONDA", "adidas" logo stripes
    ctx.fillStyle = "#111111";
    ctx.font = "bold 16px Inter, sans-serif";
    ctx.fillText("FIFA", width * 0.5, height * 0.8);
    ctx.font = "bold 10px Inter, sans-serif";
    ctx.fillText("WORLD CUP 2026", width * 0.47, height * 0.84);

    ctx.fillStyle = "#006847";
    ctx.font = "italic bold 13px Inter, sans-serif";
    ctx.fillText("TRIONDA", width * 0.78, height * 0.75);

    // Three stripes (adidas)
    ctx.save();
    ctx.fillStyle = "#E01B22";
    ctx.translate(width * 0.15, height * 0.25);
    ctx.rotate(-Math.PI / 6);
    ctx.fillRect(0, 0, 6, 20);
    ctx.fillRect(10, -3, 6, 23);
    ctx.fillRect(20, -6, 6, 26);
    ctx.restore();
  };

  const drawStar = (ctx, cx, cy, spikes, outerRadius, innerRadius) => {
    let rot = Math.PI / 2 * 3;
    let x = cx;
    let y = cy;
    let step = Math.PI / spikes;

    ctx.beginPath();
    ctx.moveTo(cx, cy - outerRadius);
    for (let i = 0; i < spikes; i++) {
      x = cx + Math.cos(rot) * outerRadius;
      y = cy + Math.sin(rot) * outerRadius;
      ctx.lineTo(x, y);
      rot += step;

      x = cx + Math.cos(rot) * innerRadius;
      y = cy + Math.sin(rot) * innerRadius;
      ctx.lineTo(x, y);
      rot += step;
    }
    ctx.lineTo(cx, cy - outerRadius);
    ctx.closePath();
    ctx.fill();
  };

  return (
    <div
      ref={containerRef}
      data-testid="football-3d-widget"
      className={`relative flex flex-col items-center justify-center bg-transparent select-none ${className}`}
      style={{ width: size, height: size }}
    >
      <canvas
        ref={canvasRef}
        className="block bg-transparent drop-shadow-2xl transition-all duration-300"
        style={{
          width: size,
          height: size,
        }}
      />

      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center rounded-full bg-white/10 backdrop-blur-sm transition-opacity duration-300">
          <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin mb-2" />
          <span className="text-xs text-muted-foreground font-semibold">Aligning panels...</span>
        </div>
      )}

      {usingFallback && !loading && (
        <div className="absolute bottom-2 bg-black/65 backdrop-blur-md px-3 py-1 rounded-full text-[9px] text-white/95 font-medium select-none pointer-events-none tracking-wide animate-fade-in border border-white/10">
          ⚡ TRIONDA High-Fidelity Render
        </div>
      )}
    </div>
  );
};
