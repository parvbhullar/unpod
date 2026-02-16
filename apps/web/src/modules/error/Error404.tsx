'use client';
import styled from 'styled-components';
import { Button } from 'antd';
import { useRouter } from 'next/navigation';
import { useIntl } from 'react-intl';

export const StyledError404 = styled.div`
  width: 100%;
  height: 85vh;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  font-family: ${({ theme }) => theme.font.family};

  h1 {
    font-size: 160px;
    font-weight: ${({ theme }) => theme.font.weight.bold};
    margin: 0;
  }

  h3 {
    margin: 0;
    font-size: 30px;
    position: relative;
    top: -20px;
  }
`;

type Error404Props = {
  path?: string;
  title?: string;
};

export default function Error404({ path, title }: Error404Props) {
  const router = useRouter();
  const { formatMessage } = useIntl();
  const goToHome = () => {
    if (path) {
      router.replace(path);
    } else {
      router.back();
    }
  };
  return (
    <StyledError404>
      <h1>404</h1>
      <h3>{title || formatMessage({ id: 'common.pageNotFound' })}</h3>
      <Button type="primary" onClick={goToHome} style={{ marginTop: 24 }}>
        {formatMessage({ id: 'common.goBack' })}
      </Button>
    </StyledError404>
  );
}
