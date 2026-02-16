import Button from '../../components/Button';
import styled, { keyframes } from 'styled-components';

import { TrackToggle } from './TrackToggle';
import { FaStop } from 'react-icons/fa';
import { Avatar, Badge, Card, Flex, Typography } from 'antd';
import { AppStatusBadge } from '@unpod/components/common/AppStatusBadge';
import { ConnectionState } from 'livekit-client';

const { Title, Text } = Typography;

const wave = keyframes`
  0% {
    transform: scaleY(1);
  }
  50% {
    transform: scaleY(1.7);
  }
  100% {
    transform: scaleY(1);
  }
`;

export const VoiceWave = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 28px;

  .bar {
    width: 4px;
    background: #555454;
    border-radius: 4px;
    animation: ${wave} 0.9s ease-in-out infinite;

    /* IMPORTANT */
    transform-origin: center;
  }

  /* RiVoiceprint style base shape */

  .bar:nth-child(1) {
    height: 8px;
    animation-delay: 0s;
  }

  .bar:nth-child(2) {
    height: 14px;
    animation-delay: 0.12s;
  }

  .bar:nth-child(3) {
    height: 20px;
    animation-delay: 0.24s;
  }

  .bar:nth-child(4) {
    height: 14px;
    animation-delay: 0.36s;
  }

  .bar:nth-child(5) {
    height: 8px;
    animation-delay: 0.48s;
  }
`;

const FlexContainer = styled.div`
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  width: 100%;
`;

const StyledButton = styled(Button)`
  width: 100%;
  justify-content: center;
  align-items: center;
  margin: 20px 0;
  border-radius: 12px !important;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  height: 51px !important;

  border: 1px solid red;
  background-color: transparent;
  color: red;

  &:hover {
    background-color: #edb0b6;
    color: red;
  }
`;

const StyledTrackToggle = styled(TrackToggle)`
  border: ${({ theme }) => `1px solid ${theme?.palette.primary}`};
  border-radius: 50%;
  height: 40px !important;
  width: 40px !important;
  background-color: ${({ theme }) => theme?.palette.primary} !important;
  color: white;

  &:hover {
    background-color: ${({ theme }) => theme?.palette.primary} !important;
  }
`;

export const ConfigurationPanelItem = ({
                                         roomState,
                                         children,
                                         onConnectClicked,
                                         agentName,
                                         count = 0,
                                         duration,
                                         turns,
                                         avgLatency,
                                         state,
                                       }) => {
  const metrics = [
    {
      label: 'Duration',
      value: duration,
    },
    {
      label: 'Turns',
      value: turns,
    },
    {
      label: 'Avg Latency',
      value: avgLatency,
    },
  ];

  const statusColors = {
    success: {
      color: 'badge-success',
      label: (
        <Flex align="center" gap={6}>
          {!state && <Badge dot status="success" />}
          <Typography.Text>{state ? `${state} ...` : 'Live'}</Typography.Text>
        </Flex>
      ),
    },
  };

  return (
    <FlexContainer>
      <>{children}</>
      {/*{roomState === ConnectionState.Connected && (*/}
      {/*  <StyledTrackToggle source={Track.Source.Microphone} />*/}
      {/*)}*/}
      {/*{roomState === ConnectionState.Connected && (*/}
      <Card
        style={{ width: '100%' }}
        styles={{
          body: {
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          },
        }}
      >
        <Flex align="center" justify="space-between">
          <Text>Current Test</Text>
          <AppStatusBadge
            status="success"
            size={'small'}
            shape={'round'}
            animate={true}
            name={state && state}
            statusColors={!state && statusColors}
          />

          {/*</AppStatusBadge>*/}
        </Flex>
        <Flex align="flex-start" gap={12}>
          <Avatar
            size={44}
            shape="square"
            style={{
              fontSize: 20,
              background: 'linear-gradient(135deg, #00d4ff ,#a855f7)',
            }}
          >
            🎙️
          </Avatar>
          <Flex align="flex-start" vertical>
            <Title level={5} className="mb-0">
              {agentName}
            </Title>
            <Text>{count}</Text>
          </Flex>
        </Flex>

        <VoiceWave>
          <div className="bar" />
          <div className="bar" />
          <div className="bar" />
          <div className="bar" />
          <div className="bar" />
        </VoiceWave>

        <Flex gap={12} align={'center'} justify="center">
          {metrics.map((item, index) => (
            <Card
              key={index}
              size="small"
              style={{
                minWidth: 90,
                textAlign: 'center',
                borderRadius: 10,
              }}
            >
              <Title level={5} style={{ margin: 0 }}>
                {item.value}
              </Title>
              <Text type="secondary" style={{ fontSize: 11 }}>
                {item.label}
              </Text>
            </Card>
          ))}
        </Flex>

        <StyledButton
          variant="outlined"
          danger
          icon={<FaStop size={12} />}
          onClick={onConnectClicked}
        >
          End Test
        </StyledButton>
      </Card>
      {/*)}*/}
    </FlexContainer>
  );
};
