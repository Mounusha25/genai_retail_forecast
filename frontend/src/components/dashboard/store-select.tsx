"use client";

export function StoreSelect({
  stores,
  value,
  onChange,
  label,
}: {
  stores: string[];
  value: string;
  onChange: (value: string) => void;
  label: string;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs text-neutral-400">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-white/30"
      >
        {stores.map((store) => (
          <option key={store} value={store} className="bg-neutral-900">
            {store}
          </option>
        ))}
      </select>
    </label>
  );
}
