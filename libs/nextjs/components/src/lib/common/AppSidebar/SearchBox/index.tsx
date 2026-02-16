import React, { memo, useState } from 'react';
import { MdSearch } from 'react-icons/md';
import { debounce } from 'lodash';
import { StyledInput } from './index.styled';
import { useIntl } from 'react-intl';
import { InputProps } from 'antd';

type SearchBoxProps = Omit<InputProps, 'onSearch'> & {
  onSearch: (value: string) => void;};

const SearchBox: React.FC<SearchBoxProps> = ({ onSearch, ...props }) => {
  const { formatMessage } = useIntl();
  const [searchStr, setSearchStr] = useState('');

  const debounceFun = debounce((str: string) => {
    onSearch(str);
  }, 300);

  const onSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const keyword = event.target.value;

    setSearchStr(keyword);
    if (keyword) {
      if (keyword.length > 2) debounceFun(keyword);
      else onSearch('');
    } else {
      debounceFun(keyword);
    }
  };

  return (
    <StyledInput
      placeholder={formatMessage({ id: 'common.searchHere' })}
      size="large"
      value={searchStr}
      onChange={onSearchChange}
      prefix={<MdSearch fontSize={20} />}
      {...props}
    />
  );
};

export default memo(SearchBox);
