import { useTranslation } from "react-i18next";
import { CountdownBar } from "./CountdownBar";

interface Props {
  onReset: () => void;
  offlineQueued?: boolean;
}

export function ThankYouScreen({ onReset, offlineQueued = false }: Props) {
  const { t } = useTranslation();

  return (
    <div
      className="flex flex-col items-center justify-center min-h-screen bg-kiosk-bg px-8 py-12"
      role="main"
      aria-live="polite"
    >
      <div className="max-w-2xl w-full text-center flex flex-col items-center gap-8">
        <div
          className="w-32 h-32 rounded-full bg-kiosk-yes/10 flex items-center justify-center animate-bounce-once"
          aria-hidden="true"
        >
          <span className="text-6xl">✅</span>
        </div>

        <div>
          <h1 className="text-4xl font-bold text-kiosk-text-primary mb-4">
            {t("kiosk.thankyou.heading")}
          </h1>
          <p className="text-xl text-kiosk-text-secondary">
            {t(offlineQueued ? "kiosk.thankyou.subtextQueued" : "kiosk.thankyou.subtext")}
          </p>
        </div>

        <div className="w-full">
          <CountdownBar seconds={10} onComplete={onReset} />
        </div>
      </div>
    </div>
  );
}
