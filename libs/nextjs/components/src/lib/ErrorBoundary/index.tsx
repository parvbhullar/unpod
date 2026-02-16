'use client';

import React, { ErrorInfo, ReactNode } from 'react';
import { Alert, Button } from 'antd';
import { injectIntl, IntlShape } from 'react-intl';

type ErrorBoundaryProps = {
  children: ReactNode;
  intl: IntlShape;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onReset?: () => void;
  fallback?:
    | ReactNode
    | ((error: Error | null, reset: () => void) => ReactNode);
  title?: string;
  description?: string;
  showError?: boolean;
  resetText?: string;};

type ErrorBoundaryState = {
  hasError: boolean;
  error: Error | null;};

class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Call optional onError callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  override render(): ReactNode {
    const { intl } = this.props;
    const { formatMessage } = intl;

    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return typeof this.props.fallback === 'function'
          ? this.props.fallback(this.state.error, this.handleReset)
          : this.props.fallback;
      }

      // Default fallback UI
      return (
        <div style={{ padding: 20 }}>
          <Alert
            message={
              this.props.title || formatMessage({ id: 'errorBoundary.title' })
            }
            description={
              this.props.showError
                ? this.state.error?.message ||
                  formatMessage({ id: 'errorBoundary.unexpected' })
                : this.props.description ||
                  formatMessage({ id: 'errorBoundary.description' })
            }
            type="error"
            showIcon
            action={
              <Button size="small" onClick={this.handleReset}>
                {this.props.resetText ||
                  formatMessage({ id: 'errorBoundary.tryAgain' })}
              </Button>
            }
          />
        </div>
      );
    }

    return this.props.children;
  }
}

export default injectIntl(ErrorBoundary);
