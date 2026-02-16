import styled from 'styled-components';

export const StyledFeaturesWrapper = styled.div`
  position: relative;
  display: flex;
  flex-wrap: wrap;
`;

export const StyledFeaturesContent = styled.div`
  width: 72%;
  padding-right: 30px;
  position: sticky;
  top: 30px;
  bottom: 0;
  z-index: 2;
  align-self: flex-start;
  padding-top: 50px;
  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    width: 60%;
  }
  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    width: 100%;
    padding-right: 0;
    position: relative;
    top: auto;
    bottom: auto;
  }

  .scrollspy__menu {
    padding-left: 0;
    margin: 0 0 30px;
    list-style: none;
    position: relative;
    min-height: 550px;

    li {
      position: absolute;
      left: 0;
      top: 0;
      z-index: 1;
      width: 100%;
      height: 100%;
      visibility: hidden;
      opacity: 0;
      @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
        position: relative;
        left: auto;
        top: auto;
        visibility: visible;
        opacity: 1;
        margin-bottom: 20px;
      }

      a {
        display: flex;
        flex-direction: column;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
        border-radius: 18px;
        color: #000;
        background-color: #fff;

        .ant-image {
          width: 100%;
          //margin-bottom: 12px;
          max-height: 525px;

          .ant-image-img {
            height: 100%;
            width: 100%;
          }
        }
      }

      &.is-current {
        visibility: visible;
        opacity: 1;
      }
    }
  }
`;

export const StyledFeaturesPanel = styled.div`
  padding-bottom: 100px;
  width: 28%;
  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    width: 40%;
  }
  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    width: 100%;
  }

  .scrollspy__menu {
    padding-left: 0;
    margin: 0;
    list-style: none;
    position: relative;

    li {
      margin-bottom: 36px;

      &.is-current {
        .feature-content {
          background-color: #000;
          color: #fff;

          h5,
          article {
            color: #fff !important;
          }

          &:before {
            opacity: 1;
            visibility: visible;
            border-right-color: #000;
          }
        }
      }
    }
  }
`;
