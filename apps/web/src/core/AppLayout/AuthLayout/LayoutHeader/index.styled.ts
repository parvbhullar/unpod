'use client';
import styled from 'styled-components';
import { Layout } from 'antd';

const { Header } = Layout;

export const StyledHeader = styled(Header)`
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  line-height: 1;
  background: transparent;
`;

export const StyledHeaderContainer = styled.div`
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
`;

export const StyledLogo = styled.div`
  font-weight: bold;
  font-size: 20px;
  color: ${({ theme }) => theme.palette.primary};

  img {
    cursor: pointer;
    height: 32px;
  }
`;

export const StyledMenu = styled.ul`
  display: flex;
  min-width: 0;
  margin: 0;
  list-style: none;
  padding: 0;
  line-height: 32px;

  & > li {
    padding-inline: 16px;

    & > a {
      color: ${({ theme }) => theme.palette.text.primary};
      &:hover {
        color: ${({ theme }) => theme.palette.primary};
      }
    }
  }
`;
