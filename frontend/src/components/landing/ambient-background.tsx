export function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 z-0" aria-hidden>
      <div
        className="absolute -top-1/4 right-[-15%] h-[80vh] w-[80vh] rounded-full opacity-[0.16] blur-[160px]"
        style={{ background: "radial-gradient(circle, #3987e5 0%, #3987e5 25%, transparent 75%)" }}
      />
      <div
        className="absolute bottom-[-25%] left-[-15%] h-[75vh] w-[75vh] rounded-full opacity-[0.14] blur-[160px]"
        style={{ background: "radial-gradient(circle, #9085e9 0%, #9085e9 25%, transparent 75%)" }}
      />
    </div>
  );
}
