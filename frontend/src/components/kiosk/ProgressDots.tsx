interface Props {
  total: number;
  current: number;
}

export function ProgressDots({ total, current }: Props) {
  return (
    <div
      className="flex items-center justify-center gap-2"
      role="progressbar"
      aria-valuenow={current + 1}
      aria-valuemin={1}
      aria-valuemax={total}
      aria-label={`Kysymys ${current + 1} / ${total}`}
    >
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={`rounded-full transition-all duration-300 ${
            i === current
              ? "w-3 h-3 bg-kiosk-primary"
              : i < current
              ? "w-2 h-2 bg-kiosk-primary/40"
              : "w-2 h-2 bg-kiosk-border"
          }`}
          aria-hidden="true"
        />
      ))}
    </div>
  );
}
