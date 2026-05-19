import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error): void {
    console.error("Unhandled error:", error.message);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div
          className="min-h-screen flex items-center justify-center bg-kiosk-bg p-8"
          role="alert"
          aria-live="assertive"
        >
          <div className="text-center max-w-md">
            <div className="text-6xl mb-6">⚠️</div>
            <h1 className="text-2xl font-semibold text-kiosk-text-primary mb-4">
              Jokin meni pieleen
            </h1>
            <p className="text-lg text-kiosk-text-secondary">
              Pyydä hoitajaa käynnistämään laite uudelleen.
            </p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
