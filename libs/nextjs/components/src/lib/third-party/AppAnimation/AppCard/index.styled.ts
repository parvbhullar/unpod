import {Card} from 'antd';
import styled from 'styled-components';

export const StyledCard = styled(Card)`
  position: relative;
  box-shadow: ${({theme}) => theme.component.card.boxShadow} !important;
  border-radius: ${({theme}) => theme.component.card.borderRadius};
  display: flex;
  flex-direction: column;
  background: ${({theme}) => theme.palette.background.default};
  color: ${({theme}) => theme.palette.text.primary};

  & .ant-card-head-title {
    color: ${({theme}) => theme.palette.text.primary};
  }

  & > .ant-card-head {
    min-height: 10px;
    font-weight: ${({theme}) => theme.font.weight.bold};
    padding-left: 20px;
    padding-right: 20px;
    border-bottom: 0 none;
    margin-bottom: 0;

    & .ant-card-head-title {
      line-height: 1.4993rem;
      padding-bottom: 4px;
    }

    & .ant-card-extra {
      padding-bottom: 4px;
      padding-top: 16px !important;

      & a {
        color: ${({theme}) => theme.palette.secondary};
      }
    }
  }

  & > .ant-card-body {
    padding: 16px 20px;
  }

  &.heightFull {
    height: 100%;

    & .ant-card-body {
      flex: 1;
    }
  }

  & .ant-card-actions {
    background-color: transparent;
    padding-top: 16px !important;
  }

  &.no-card-space {
    & .ant-card-body {
      padding: 0;
    }
  }

  &.no-card-space-ltr-rtl {
    & .ant-card-body {
      padding-left: 0;
      padding-right: 0;
    }
  }
`;
