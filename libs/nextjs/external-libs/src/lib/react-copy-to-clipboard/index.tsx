import React, { ReactElement } from 'react';
import { CopyOptions, copyToClipboard } from './copy-to-clipboard';

export type CopyToClipboardProps = {
  text: string;
  children: ReactElement<any>;
  onCopy?: (text: string, result: boolean) => void;
  options?: CopyOptions;};

export class CopyToClipboard extends React.PureComponent<CopyToClipboardProps> {
  handleClick = (event: React.MouseEvent): void => {
    const { text, onCopy, children, options } = this.props;

    const elem = React.Children.only(children);

    const result = copyToClipboard(text, options);

    if (onCopy) {
      onCopy(text, result);
    }

    // Bypass onClick if it was present
    if (elem && elem.props && typeof elem.props.onClick === 'function') {
      elem.props.onClick(event);
    }
  };

  override render(): ReactElement {
    const {
      text: _text,
      onCopy: _onCopy,
      options: _options,
      children,
      ...props
    } = this.props;
    const elem = React.Children.only(children);

    return React.cloneElement(elem, { ...props, onClick: this.handleClick });
  }
}
