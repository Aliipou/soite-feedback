import { useTranslation } from "react-i18next";
import { face4Colors, face4Emojis } from "../../styles/tokens";

interface Props {
  onSelect: (value: number) => void;
}

const DISPLAY_ORDER = [4, 3, 2, 1] as const;

export function Face4Input({ onSelect }: Props) {
  const { t } = useTranslation();

  return (
    <div
      className="flex gap-3 sm:gap-6 justify-center w-full"
      role="group"
      aria-label={t("kiosk.face4.label")}
    >
      {DISPLAY_ORDER.map((value) => (
        <button
          key={value}
          type="button"
          onClick={() => onSelect(value)}
          className="flex flex-col items-center gap-3 p-4 sm:p-6 rounded-3xl border-2 border-kiosk-border bg-white active:scale-95 transition-all duration-150 flex-1 shadow-sm focus:outline-none focus:ring-4 focus:ring-offset-2"
          style={
            {
              "--tw-ring-color": face4Colors[value],
            } as React.CSSProperties
          }
          aria-label={t(`kiosk.face4.${value}`)}
          onPointerEnter={(e) => {
            const el = e.currentTarget;
            el.style.borderColor = face4Colors[value];
            el.style.backgroundColor = `${face4Colors[value]}18`;
          }}
          onPointerLeave={(e) => {
            const el = e.currentTarget;
            el.style.borderColor = "";
            el.style.backgroundColor = "";
          }}
        >
          <span className="text-6xl sm:text-7xl leading-none" role="img" aria-hidden="true">
            {face4Emojis[value]}
          </span>
          <span
            className="text-sm sm:text-base text-center text-kiosk-text-secondary leading-tight font-semibold"
            style={{ color: face4Colors[value] }}
          >
            {t(`kiosk.face4.${value}`)}
          </span>
        </button>
      ))}
    </div>
  );
}
