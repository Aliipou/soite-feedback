import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  seconds: number;
  onComplete: () => void;
}

export function CountdownBar({ seconds, onComplete }: Props) {
  const { t } = useTranslation();
  const [remaining, setRemaining] = useState(seconds);

  useEffect(() => {
    setRemaining(seconds);
  }, [seconds]);

  useEffect(() => {
    if (remaining <= 0) {
      onComplete();
      return;
    }
    const id = setTimeout(() => setRemaining((r) => r - 1), 1000);
    return () => clearTimeout(id);
  }, [remaining, onComplete]);

  const pct = (remaining / seconds) * 100;

  return (
    <div className="w-full">
      <p className="text-sm text-kiosk-text-secondary text-center mb-2">
        {t("kiosk.thankyou.countdown", { seconds: remaining })}
      </p>
      <div
        className="w-full h-2 bg-kiosk-border rounded-full overflow-hidden"
        role="progressbar"
        aria-valuenow={remaining}
        aria-valuemin={0}
        aria-valuemax={seconds}
        aria-label={`Nollautuu ${remaining} sekunnissa`}
      >
        <div
          className="h-full bg-kiosk-primary rounded-full transition-all duration-1000 ease-linear"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
