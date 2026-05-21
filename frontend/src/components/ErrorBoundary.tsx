import React from 'react';
import { captureError } from '@/lib/sentry';

interface Props {
  children: React.ReactNode;
  /** Optional label used in logs (e.g. route name). */
  name?: string;
  /** When this value changes, the boundary clears its error state.
   * Pass a route key here to reset automatically on navigation. */
  resetKey?: string | number;
  /** Render a smaller in-page fallback instead of the full-screen one.
   * Use for per-page boundaries inside an app shell. */
  inline?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Always log to console so dev sees the stack trace locally even
    // without a Sentry DSN configured.
    console.error(
      `[ErrorBoundary${this.props.name ? `:${this.props.name}` : ''}]`,
      error,
      info,
    );
    // Ship to Sentry. No-op when Sentry isn't initialized (#64).
    captureError(error, {
      boundary: this.props.name ?? 'root',
      componentStack: info.componentStack,
    });
  }

  componentDidUpdate(prevProps: Props) {
    if (this.state.hasError && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ hasError: false, error: null });
    }
  }

  reset = () => this.setState({ hasError: false, error: null });

  render() {
    if (!this.state.hasError) return this.props.children;

    if (this.props.inline) {
      return (
        <div className="bg-white rounded-lg shadow p-6 text-center my-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">
            Diese Seite konnte nicht geladen werden
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            Ein unerwarteter Fehler ist aufgetreten. Sie können es erneut
            versuchen oder zu einem anderen Bereich navigieren.
          </p>
          <button onClick={this.reset} className="btn btn-primary">
            Erneut versuchen
          </button>
        </div>
      );
    }

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Etwas ist schiefgelaufen
          </h1>
          <p className="text-gray-500 mb-6">
            Ein unerwarteter Fehler ist aufgetreten. Bitte laden Sie die Seite neu.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="btn btn-primary"
          >
            Seite neu laden
          </button>
        </div>
      </div>
    );
  }
}
