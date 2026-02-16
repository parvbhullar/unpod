import { useState } from 'react';
import { Typography } from 'antd';
import styled from 'styled-components';
import { StyledRoot } from './index.styled';
import { AppDrawer } from '@unpod/components/antd';
import { AppHeaderButton } from '@unpod/components/common/AppPageHeader';
import AppSpaceCallModal from '@unpod/components/modules/AppSpaceContactCall/AppSpaceCallModal';
import { useAppSpaceActionsContext } from '@unpod/providers';
import { MdCall, MdSchedule } from 'react-icons/md';
import DocSelector from './DocSelector';
import { useIntl } from 'react-intl';

const EmptyStateRoot = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 74px);

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 12px;
  }
`;

const EmptyStateCard = styled.div`
  display: flex;
  flex-direction: column;
  padding: 16px;
  background-color: ${({ theme }) => theme.palette.background.default};
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 16px;
  cursor: pointer;
  max-width: 400px;
  width: 100%;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${({ theme }) => theme.palette.background.component};
  }
`;

const IconWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 12px;

  svg {
    font-size: 24px;
  }

  & .ant-typography {
    margin: 0 !important;
  }
`;

const { Paragraph, Title } = Typography;

const LandingView = () => {
  const { formatMessage } = useIntl();

  const [open, setOpen] = useState(false);
  const [visible, setVisible] = useState(false);
  const { callsActions } = useAppSpaceActionsContext();
  const isMobile =
    typeof window !== 'undefined' ? window.innerWidth <= 576 : false;
  const onFinishSchedule = () => {
    callsActions?.reCallAPI?.();
  };
  return (
    <>
      <StyledRoot>
        <EmptyStateRoot>
          <EmptyStateCard onClick={() => setOpen(true)}>
            <IconWrapper>
              <MdSchedule />
              <Title level={4}>
                {formatMessage({ id: 'call.landingViewTitle' })}
              </Title>
            </IconWrapper>
            <Paragraph className="mb-0">
              {formatMessage({ id: 'call.landingViewDes' })}
            </Paragraph>
          </EmptyStateCard>
        </EmptyStateRoot>
      </StyledRoot>
      <AppDrawer
        open={open}
        onClose={() => setOpen(false)}
        closable={false}
        title={formatMessage({ id: 'call.landingViewDrawerTitle' })}
        padding="0"
        extra={
          <AppHeaderButton
            type="primary"
            shape={!isMobile ? 'round' : 'circle'}
            icon={
              <span className="anticon" style={{ verticalAlign: 'middle' }}>
                <MdCall fontSize={!isMobile ? 16 : 22} />
              </span>
            }
            onClick={() => setVisible(true)}
          >
            {!isMobile && formatMessage({ id: 'spaceHeader.callNow' })}
          </AppHeaderButton>
        }
      >
        <DocSelector allowSelection />
      </AppDrawer>

      <AppSpaceCallModal
        open={visible}
        setOpen={setVisible}
        idKey="document_id"
        onFinishSchedule={onFinishSchedule}
      />
    </>
  );
};

export default LandingView;
