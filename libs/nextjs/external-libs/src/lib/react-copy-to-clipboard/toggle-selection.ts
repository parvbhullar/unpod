export const deselectCurrent = (): (() => void) => {
  const selection = document.getSelection();

  if (!selection || selection.rangeCount === 0) {
    return () => undefined;
  }

  const activeElement = document.activeElement as HTMLElement | null;
  const ranges = Array.from({length: selection.rangeCount}, (_, i) =>
    selection.getRangeAt(i),
  );

  let previousActive: HTMLElement | null = null;

  if (
    activeElement &&
    ['INPUT', 'TEXTAREA'].includes(activeElement.tagName.toUpperCase())
  ) {
    previousActive = activeElement;
    activeElement.blur();
  }

  selection.removeAllRanges();

  return () => {
    if (selection.type === 'Caret') {
      selection.removeAllRanges();
    }

    if (selection.rangeCount === 0) {
      ranges.forEach((range) => selection.addRange(range));
    }

    previousActive?.focus();
  };
};
