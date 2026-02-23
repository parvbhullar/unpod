import {useEffect, useRef, useState} from 'react';
import {StyledInput} from './index.styled';
import {useDebounceValue} from '@unpod/custom-hooks';
import {MdSearch} from 'react-icons/md';
import {useIntl} from 'react-intl';
import type {InputRef} from 'antd';
import type {Spaces} from '@unpod/constants/types';

type SearchBoxProps = {
  setSearch: (value: string) => void;
  search: string;
  currentSpace: Spaces | null;
  searchCount: number;
};

const SearchBox = ({
                     setSearch,
                     search,
                     currentSpace,
                     searchCount,
                   }: SearchBoxProps) => {
  const {formatMessage} = useIntl();
  const [searchStr, setSearchStr] = useState('');
  const inputRef = useRef<InputRef | null>(null);

  const serchValue = useDebounceValue(searchStr, 500);

  useEffect(() => {
    if (search !== searchStr) setSearch(serchValue);
  }, [serchValue]);

  useEffect(() => {
    setSearchStr(search);
  }, [search]);

  useEffect(() => {
    if (currentSpace?.token) {
      setSearch('');
    }
  }, [currentSpace?.token]);

  useEffect(() => {
    setTimeout(() => {
      inputRef.current?.focus({
        cursor: 'end',
      });
    }, 100);
  }, [searchCount]);

  return (
    <StyledInput
      placeholder={formatMessage({id: 'common.searchHere'})}
      variant="borderless"
      size="large"
      value={searchStr}
      onChange={(e) => setSearchStr(e.target.value)}
      ref={inputRef}
      prefix={<MdSearch size={21} color={'#bbb'}/>}
    />
  );
};

export default SearchBox;
