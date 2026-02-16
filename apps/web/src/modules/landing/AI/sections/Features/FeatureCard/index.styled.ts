import styled from 'styled-components';

export const StyledFeatureCardWrapper = styled.div`
  box-shadow: 0px 0px 30px 10px rgba(160, 165, 185, 0.1);
  font-weight: 500;
  font-size: 14px;
  color: #757575;
  background-color: #fff;
  border-radius: 10px;
`;

export const StyledFeatureImageWrapper = styled.div`
  padding: 20px 30px;
  background-color: #5f67fa;
  color: #fff;
  border-radius: 10px 10px 0 0;
`;

export const StyledFeatureImageContent = styled.div`
  padding: 20px 30px;
  background-color: #fff;
  color: #000;
  position: relative;
  border-radius: 0 0 10px 10px;

  h5 {
    font-weight: bold;
  }

  h5,
  article {
    color: #000 !important;
  }

  &:before {
    content: '';
    position: absolute;
    left: -10px;
    top: 20px;
    z-index: 1;
    width: 0;
    height: 0;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
    border-right: 10px solid #f0f1f7;
    opacity: 0;
    visibility: hidden;
  }
`;
