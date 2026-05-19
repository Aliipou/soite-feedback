interface Props {
  onSelect: (lang: "fi" | "sv") => void;
}

export function LanguageSelectScreen({ onSelect }: Props) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-kiosk-bg px-8 py-12">
      <div className="max-w-2xl w-full text-center">
        <div className="text-9xl mb-8" role="img" aria-label="Soite">
          💙
        </div>

        <p className="text-2xl text-kiosk-text-secondary mb-12 font-medium">
          Valitse kieli / Välj språk
        </p>

        <div className="flex flex-col sm:flex-row gap-6">
          <button
            type="button"
            onClick={() => onSelect("fi")}
            className="flex-1 py-10 text-4xl font-bold text-white bg-kiosk-primary hover:bg-kiosk-primary-hover active:scale-95 rounded-3xl transition-all duration-150 focus:outline-none focus:ring-4 focus:ring-offset-2 focus:ring-kiosk-primary/50 shadow-lg"
            autoFocus
            lang="fi"
          >
            Suomi
          </button>
          <button
            type="button"
            onClick={() => onSelect("sv")}
            className="flex-1 py-10 text-4xl font-bold text-white bg-kiosk-primary hover:bg-kiosk-primary-hover active:scale-95 rounded-3xl transition-all duration-150 focus:outline-none focus:ring-4 focus:ring-offset-2 focus:ring-kiosk-primary/50 shadow-lg"
            lang="sv"
          >
            Svenska
          </button>
        </div>
      </div>
    </div>
  );
}
