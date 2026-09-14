interface StatCardProps {
  label: string;
  value: string;
  tone?: "default" | "positive" | "negative";
  sublabel?: string;
}

export default function StatCard({ label, value, tone = "default", sublabel }: StatCardProps) {
  const toneClass = tone === "positive" ? "text-ok" : tone === "negative" ? "text-danger" : "text-ink";
  return (
    <div className="bg-white border border-line rounded-lg px-5 py-4">
      <div className="text-xs uppercase tracking-wide text-muted mb-2">{label}</div>
      <div className={`money text-2xl ${toneClass}`}>{value}</div>
      {sublabel && <div className="text-xs text-muted mt-1">{sublabel}</div>}
    </div>
  );
}
