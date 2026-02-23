import {useEffect, useState} from 'react';

export const useAutoComplete = () => {
  const [filled, setFilled] = useState<boolean>(false);

  useEffect(() => {
    function handleAutoComplete(e: any) {
      setFilled(
        e.target.hasAttribute('autocompleted') &&
        e.target.type !== 'file' &&
        e.target.type !== 'checkbox' &&
        e.target.type !== 'radio',
      );
      // e.preventDefault(); // prevent autocomplete
    }

    document.addEventListener('onautocomplete', handleAutoComplete);

    return () =>
      document.removeEventListener('onautocomplete', handleAutoComplete);
  }, []);

  return {filled, setFilled} as const;
};
