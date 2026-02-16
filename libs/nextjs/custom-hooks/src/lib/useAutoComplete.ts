'use client';

import { Dispatch, SetStateAction, useEffect, useState } from 'react';

export type AutoCompleteResult = {
  filled: boolean;
  setFilled: Dispatch<SetStateAction<boolean>>;};

type AutocompleteEvent = Event & {
  target: HTMLInputElement & EventTarget;};

export const useAutoComplete = (): AutoCompleteResult => {
  const [filled, setFilled] = useState<boolean>(false);

  useEffect(() => {
    function handleAutoComplete(e: Event): void {
      const event = e as AutocompleteEvent;
      console.info('onautocomplete: ', event.target.type);
      setFilled(
        event.target.hasAttribute('autocompleted') &&
          event.target.type !== 'file' &&
          event.target.type !== 'checkbox' &&
          event.target.type !== 'radio',
      );
      // e.preventDefault(); // prevent autocomplete
    }

    document.addEventListener('onautocomplete', handleAutoComplete);

    return () =>
      document.removeEventListener('onautocomplete', handleAutoComplete);
  }, []);

  return { filled, setFilled };
};
