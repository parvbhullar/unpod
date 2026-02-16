import React from 'react';
import { Button } from 'antd';
import { MdChevronLeft, MdChevronRight } from 'react-icons/md';
import { StyledPagination } from './index.styled';

interface ThumbPaginationProps {
  page: number;
  setPage: (page: number) => void;
  numPages: number;
}

const ThumbPagination: React.FC<ThumbPaginationProps> = ({ page, setPage, numPages }) => {
  const disableLeft = page === 0;
  const disableRight = page === numPages - 1;
  // const pinnedTrack = usePinnedTrack();

  const nextPage = () => {
    setPage(Math.min(page + 1, numPages - 1));
  };
  const prevPage = () => {
    setPage(Math.max(page - 1, 0));
  };
  return (
    <StyledPagination>
      <Button
        type="default"
        shape="circle"
        size="small"
        disabled={disableLeft}
        onClick={prevPage}
        style={{ cursor: disableLeft ? 'not-allowed' : 'pointer' }}
      >
        <MdChevronLeft width={16} height={16} />
      </Button>
      {/*<StyledPagination.Dots>
        {!pinnedTrack &&
          numPages < 8 &&
          [...Array(numPages)].map((_, i) => (
            <StyledPagination.Dot
              key={i}
              active={page === i}
              onClick={() => setPage(i)}
            />
          ))}
      </StyledPagination.Dots>*/}
      <Button
        type="default"
        shape="circle"
        size="small"
        disabled={disableRight}
        onClick={nextPage}
        style={{ cursor: disableRight ? 'not-allowed' : 'pointer' }}
      >
        <MdChevronRight width={16} height={16} />
      </Button>
    </StyledPagination>
  );
};

export default ThumbPagination;
