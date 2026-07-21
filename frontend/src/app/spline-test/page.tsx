import { SplineScene } from "@/components/landing/spline-scene";

export default function SplineTestPage() {
  return (
    <div style={{ position: "fixed", inset: 0, background: "#000" }}>
      <SplineScene scene="/scene.splinecode" className="h-full w-full" />
    </div>
  );
}
