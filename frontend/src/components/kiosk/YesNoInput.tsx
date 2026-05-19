import { useTranslation } from "react-i18next";
import { colors } from "../../styles/tokens";

interface Props {
  onSelect: (value: number) => void;
}

export function YesNoInput({ onSelect }: Props) {
  const { t } = useTranslation();

  return (
    <div
      className="flex flex-col gap-4 w-full max-w-lg mx-auto"
      role="group"
      aria-label="Kyllä tai Ei"
    >
      <button
        type="button"
        onClick={() => onSelect(1)}
        className="flex items-center justify-center gap-3 w-full rounded-2xl min-h-touch-xl text-button-lg font-semibold text-white transition-all duration-200 hover:opacity-90 active:scale-98 focus:outline-none focus:ring-4 focus:ring-offset-2"
        style={{ backgroundColor: colors.yes, focusRingColor: colors.yes } as React.CSSProperties}
        aria-label={t("kiosk.yesno.yes")}
      >
        <span aria-hidden="true">✓</span>
        {t("kiosk.yesno.yes")}
      </button>
      <button
        type="button"
        onClick={() => onSelect(0)}
        className="flex items-center justify-center gap-3 w-full rounded-2xl min-h-touch-xl text-button-lg font-semibold transition-all duration-200 hover:opacity-90 active:scale-98 focus:outline-none focus:ring-4 focus:ring-offset-2 bg-kiosk-secondary text-kiosk-text-primary border-2 border-kiosk-border"
        aria-label={t("kiosk.yesno.no")}
      >
        <span aria-hidden="true">✗</span>
        {t("kiosk.yesno.no")}
      </button>
    </div>
  );
}
