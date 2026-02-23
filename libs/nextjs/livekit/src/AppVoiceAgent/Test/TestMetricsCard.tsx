import {ReactNode} from 'react';
import {Avatar, Badge, Card, Flex, Typography} from 'antd';
import {AppStatusBadge} from '@unpod/components/common/AppStatusBadge';
import {FlexContainer, StyledButton} from './TestView.styled';
import {ResponseType} from './TestAgent';

const {Title, Text} = Typography;

type TestMetricsCardProps = {
  children?: ReactNode;
  agentName: string;
  state?: string | null;
  response?: ResponseType;
  onEndTest: () => void;
};

export const TestMetricsCard = ({
                                  children,
                                  agentName,
                                  state,
                                  response,
                                  onEndTest,
                                }: TestMetricsCardProps) => {
  const statusColors: Record<
    string,
    {
      color: string;
      label: ReactNode;
    }
  > = {
    success: {
      color: 'badge-success',
      label: (
        <Flex align="center" gap={6}>
          {!state && <Badge dot status="success"/>}
          <Text type="success">{state ? `${state}...` : 'DisConnect'}</Text>
        </Flex>
      ),
    },
  };

  return (
    <FlexContainer>
      <>{children}</>

      <Card
        style={{width: '100%'}}
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
            statusColors={statusColors}
          />
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
            <Text>Test #001</Text>
          </Flex>
        </Flex>

        <Text
          strong
          type={response?.type === 'success' ? 'success' : 'warning'}
          style={{
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          {response?.label}
        </Text>
        <Text
          strong
          style={{
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          Please wait 7 minutes and see result
        </Text>

        <StyledButton danger onClick={onEndTest}>
          End Test
        </StyledButton>
      </Card>
    </FlexContainer>
  );
};
