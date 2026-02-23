import styled from 'styled-components';

export const StyledSliderLayoutWrapper = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  .carousel-col {
    position: relative;
    @media (max-width: ${({theme}) => theme.breakpoints.lg - 1}px) {
      display: none;
    }
  }
`;

export const StyledCarouselWrapper = styled.div`
  height: 100%;

  .ant-carousel,
  .slick-list,
  .slick-track,
  .slick-slider {
    height: 100%;
  }
  .slick-slide > div,
  .slick-slide > div > div {
    height: 100%;
  }
`;

export const StyledImage = styled.img`
  display: block;
  background-size: cover;
  background-repeat: no-repeat;
  background-position: center center;
  width: 100%;
  height: 100%;
  object-fit: cover;
`;

export const StyledSliderContent = styled.div`
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 30px;
  color: #fff;
  background-color: rgba(0, 0, 0, 0.2);

  & h3 {
    font-size: 24px;
    text-align: center;
    color: inherit !important;
    margin-bottom: 32px;
    @media (max-width: ${({theme}) => theme.breakpoints.xxl}px) {
      font-size: 22px;
    }
    @media (max-width: ${({theme}) => theme.breakpoints.xl}px) {
      font-size: 20px;
    }
  }

  & h4 {
    font-size: 26px;
    color: inherit !important;
    margin-bottom: 5px;
    @media (max-width: ${({theme}) => theme.breakpoints.xxl}px) {
      font-size: 24px;
    }
    @media (max-width: ${({theme}) => theme.breakpoints.xl}px) {
      font-size: 22px;
    }
  }

  & p {
    margin-bottom: 0;
  }
`;
