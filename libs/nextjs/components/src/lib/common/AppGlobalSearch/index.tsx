import React, {useMemo} from 'react';

import {debounce} from 'lodash';
import {StyledSearch} from './index.styled';

type AppGlobalSearchProps = {
  setGlobalSearch?: (value: string) => void;
  placeholder?: string;
};

const AppGlobalSearch: React.FC<AppGlobalSearchProps> = ({
                                                           setGlobalSearch,
                                                           placeholder,
                                                         }) => {
  const onSearch = (value: string) => {
    setGlobalSearch?.(value);
  };

  const debouncedChangeHandler = useMemo(
    () => debounce((userInput: string) => setGlobalSearch?.(userInput), 1000),
    [setGlobalSearch],
  );

  function handleUserInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const userInput = event.target.value;
    debouncedChangeHandler(userInput);
  }

  return (
    <StyledSearch
      placeholder={placeholder || 'Search here...'}
      size="large"
      onSearch={onSearch}
      allowClear
      onChange={handleUserInputChange}
    />
  );
};

export default AppGlobalSearch;
