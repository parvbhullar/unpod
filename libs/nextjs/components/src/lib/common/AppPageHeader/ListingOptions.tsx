import React from 'react';
import { useAppActionsContext, useAppContext } from '@unpod/providers';
import { MdGridView, MdOutlineListAlt } from 'react-icons/md';
import { StyledListingBtn } from './index.styled';

const ListingOptions: React.FC = () => {
  const { setListingType } = useAppActionsContext();
  const { listingType } = useAppContext();

  const onMenuClick = () => {
    const key = listingType === 'grid' ? 'list' : 'grid';
    setListingType(key);
  };

  return (
    <StyledListingBtn onClick={onMenuClick} style={{ cursor: 'pointer' }}>
      {listingType === 'grid' ? (
        <MdOutlineListAlt fontSize={24} />
      ) : (
        <MdGridView fontSize={24} />
      )}
    </StyledListingBtn>
  );
};

export default ListingOptions;
