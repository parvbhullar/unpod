import { useEffect, useRef, useState } from 'react';
import { StyledInput } from './index.styled';
import { useDebounceValue } from '@unpod/custom-hooks';
import { MdSearch } from 'react-icons/md';
import { useIntl } from 'react-intl';

type SearchBoxProps = {
  setSearch: (value: string) => void;
  search: string;
  currentSpace: { token?: string };
  searchCount: number;
  loading?: boolean;
};

const SearchBox = ({
  setSearch,
  search,
  currentSpace,
  searchCount,
  loading,
}: SearchBoxProps) => {
  const { formatMessage } = useIntl();
  const [searchStr, setSearchStr] = useState('');
  const inputRef = useRef<any>(null);

  const serchValue = useDebounceValue(searchStr, 500);

  useEffect(() => {
    if (search !== searchStr) setSearch(serchValue);
  }, [serchValue]);

  useEffect(() => {
    setSearchStr(search);
  }, [search]);

  useEffect(() => {
    if (currentSpace.token) {
      setSearch('');
      //setSearchStr('');
    }
  }, [currentSpace.token]);

  useEffect(() => {
    setTimeout(() => {
      inputRef.current?.focus({
        cursor: 'end',
      });
    }, 100);
  }, [searchCount]);

  return (
    <StyledInput
      placeholder={formatMessage({ id: 'SearchBox.placeholder' })}
      variant="borderless"
      size="large"
      value={searchStr}
      onChange={(e) => setSearchStr(e.target.value)}
      ref={inputRef}
      prefix={<MdSearch size={21} color={'#bbb'} />}
    />
  );
};

export default SearchBox;
