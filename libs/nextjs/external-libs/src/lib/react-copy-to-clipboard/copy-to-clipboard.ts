import { deselectCurrent } from './toggle-selection';

type WindowWithClipboardData = Window & {
  clipboardData?: {
    clearData: () => void;
    setData: (format: string, data: string) => void;
  };
};

type ClipboardToIE11Formatting = {
  [key: string]: string;
};

const clipboardToIE11Formatting: ClipboardToIE11Formatting = {
  'text/plain': 'Text',
  'text/html': 'Url',
  default: 'Text',
};

const defaultMessage = 'Copy to clipboard: #{key}, Enter';

const getLegacyClipboardData = () =>
  (window as WindowWithClipboardData).clipboardData;

const format = (message: string): string => {
  const copyKey = /mac os x/i.test(navigator.userAgent) ? '⌘+C' : 'Ctrl+C';
  return message.replace(/#{\s*key\s*}/g, copyKey);
};

export type CopyOptions = {
  debug?: boolean;
  message?: string;
  format?: string;
  onCopy?: (clipboardData: DataTransfer | null) => void;
};

export const copyToClipboard = (
  text: string,
  options: CopyOptions = {},
): boolean => {
  let success = false;
  const debug = options.debug || false;
  let reselectPrevious: (() => void) | undefined;
  const range = document.createRange();
  const selection = document.getSelection();
  const mark = document.createElement('span');

  try {
    reselectPrevious = deselectCurrent();

    mark.textContent = text;
    mark.setAttribute('aria-hidden', 'true');

    Object.assign(mark.style, {
      all: 'unset',
      position: 'fixed',
      top: 0,
      clip: 'rect(0, 0, 0, 0)',
      whiteSpace: 'pre',
      webkitUserSelect: 'text',
      MozUserSelect: 'text',
      msUserSelect: 'text',
      userSelect: 'text',
    });

    mark.addEventListener('copy', (e: ClipboardEvent) => {
      e.stopPropagation();
      if (options.format) {
        e.preventDefault();

        if (typeof e.clipboardData === 'undefined') {
          // IE11
          if (debug) {
            console.warn('Fallback to window.clipboardData');
          }
          const formatType =
            clipboardToIE11Formatting[options.format] ||
            clipboardToIE11Formatting.default;
          const legacyClipboardData = getLegacyClipboardData();
          if (legacyClipboardData) {
            legacyClipboardData.clearData();
            legacyClipboardData.setData(formatType, text);
          }
        } else {
          // Modern browsers
          e.clipboardData?.clearData();
          e.clipboardData?.setData(options.format, text);
        }
      }

      if (options.onCopy) {
        e.preventDefault();
        options.onCopy(e.clipboardData);
      }
    });

    document.body.appendChild(mark);
    range.selectNodeContents(mark);
    selection?.addRange(range);

    const successful = document.execCommand('copy');
    if (!successful) throw new Error('copy command was unsuccessful');

    success = true;
  } catch (err) {
    if (debug) {
      console.error('execCommand failed:', err);
    }

    try {
      const legacyClipboardData = getLegacyClipboardData();
      if (!legacyClipboardData) {
        throw new Error('window.clipboardData is not available');
      }
      legacyClipboardData.setData(options.format || 'text', text);
      options.onCopy?.(null);
      success = true;
    } catch (fallbackErr) {
      if (debug) {
        console.error('IE clipboardData fallback failed:', fallbackErr);
      }
      const msg = format(options.message || defaultMessage);
      window.prompt(msg, text);
    }
  } finally {
    if (selection) {
      if (typeof selection.removeRange === 'function' && range) {
        selection.removeRange(range);
      } else {
        selection.removeAllRanges();
      }
    }

    if (mark) {
      document.body.removeChild(mark);
    }

    reselectPrevious?.();
  }

  return success;
};
