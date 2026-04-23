export function MetricCard({
  title,
  value,
  detail,
  tone,
}: {
  title: string;
  value: number;
  detail: string;
  tone?: "danger";
}) {
  return (
    <article className="metric-card">
      <p>{title}</p>
      <strong className={tone === "danger" ? "danger-text" : undefined}>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}
