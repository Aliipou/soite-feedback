import { scaleColors, scaleEmojis, scaleLabels } from "../../styles/tokens";

interface Props {
  onSelect: (value: number) => void;
  selected?: number | null;
}

export function Scale5Input({ onSelect, selected }: Props) {
  return (
    <div
      className="flex gap-3 justify-center w-full"
      role="group"
      aria-label="Arviointiasteikko 1–5"
    >
      {[1, 2, 3, 4, 5].map((value) => {
        const isSelected = selected === value;
        return (
          <button
            key={value}
            type="button"
            onClick={() => onSelect(value)}
            className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all duration-200 min-h-touch flex-1 ${
              isSelected
                ? "border-current scale-105 shadow-lg"
                : "border-kiosk-border hover:border-current hover:scale-102 bg-white"
            }`}
            style={
              isSelected
                ? { borderColor: scaleColors[value], backgroundColor: `${scaleColors[value]}15` }
                : {}
            }
            aria-label={`${value} — ${scaleLabels[value]}`}
            aria-pressed={isSelected}
          >
            <span className="text-4xl" role="img" aria-hidden="true">
              {scaleEmojis[value]}
            </span>
            <span
              className="text-xs text-center text-kiosk-text-secondary leading-tight"
              style={isSelected ? { color: scaleColors[value], fontWeight: 600 } : {}}
            >
              {scaleLabels[value]}
            </span>
          </button>
        );
      })}
    </div>
  );
}
