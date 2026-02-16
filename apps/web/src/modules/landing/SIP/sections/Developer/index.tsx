import React, { useState } from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { Typography } from 'antd';
import {
  StyledCardGrid,
  StyledCardIcon,
  StyledCardPill,
  StyledCardPills,
  StyledCardTitle,
  StyledCodeBlock,
  StyledDevCard,
  StyledTab,
  StyledTabBar,
} from './index.styled';
import {
  ApiOutlined,
  CustomerServiceOutlined,
  GlobalOutlined,
  SafetyOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;

const codeSamples = {
  js: `// Initialize Voice Bridge
import { SIPBridge } from '@sipbridge/sdk';

const bridge = new SIPBridge({
  apiKey: 'your-api-key',
  region: 'us-east-1',
});

// Connect to Voice AI
await bridge.connect({
  provider: 'openai-whisper',
  model: 'gpt-4-turbo',
  voice: 'alloy',
});

// Handle incoming calls
bridge.on('call', async (call) => {
  await call.answer();
  const response = await call.ai.process(
    'Hello! How can I help you today?'
  );
  await call.speak(response);
});`,
  py: `# Initialize Voice Bridge
from sipbridge import SIPBridge

bridge = SIPBridge(api_key='your-api-key', region='us-east-1')

# Connect to Voice AI
bridge.connect(provider='openai-whisper', model='gpt-4-turbo', voice='alloy')

# Handle incoming calls
def on_call(call):
    call.answer()
    response = call.ai.process('Hello! How can I help you today?')
    call.speak(response)

bridge.on('call', on_call)`,
  rest: `POST /v1/bridge/connect
{
  "apiKey": "your-api-key",
  "region": "us-east-1",
  "provider": "openai-whisper",
  "model": "gpt-4-turbo",
  "voice": "alloy"
}`,
};

const cardData = [
  {
    icon: <ApiOutlined />,
    title: 'Protocols',
    highlight: '#3b82f6',
    pills: ['SIP 2.0', 'WebRTC', 'RTP/SRTP', 'STUN/TURN'],
  },
  {
    icon: <CustomerServiceOutlined />,
    title: 'Audio Codecs',
    highlight: '#a856f7',
    pills: ['G.711 (PCMU/PCMA)', 'G.722', 'Opus', 'G.729'],
  },
  {
    icon: <GlobalOutlined />,
    title: 'Global Reach',
    highlight: '#38d996',
    pills: ['50+ Countries', 'Multi-Region', 'Edge Optimized', 'Low Latency'],
  },
  {
    icon: <SafetyOutlined />,
    title: 'Security',
    highlight: '#ef4443',
    pills: ['TLS 1.3', 'SRTP', 'OAuth 2.0', 'HIPAA Ready'],
  },
];

const DeveloperSection = () => {
  const [tab, setTab] = useState<keyof typeof codeSamples>('js');
  return (
    <AppPageSection
      bgColor="#fff"
      heading={
        <Title
          level={2}
          style={{
            fontWeight: 800,
            color: '#181c32',
            textAlign: 'center',
            fontSize: '2.2rem',
            marginBottom: 10,
          }}
        >
          Built For Developers
        </Title>
      }
      subHeading={
        <Text
          style={{
            color: '#6b6f81',
            fontSize: '1.11rem',
            textAlign: 'center',
            fontWeight: 400,
            marginBottom: 34,
            display: 'block',
          }}
        >
          Comprehensive APIs, SDKs, and tools designed to get you from concept
          to production in record time.
        </Text>
      }
      headerMaxWidth={1280}
      style={{ padding: '64px 0 36px 0' }}
    >
      <StyledTabBar>
        <StyledTab
          type="button"
          $active={tab === 'js'}
          onClick={() => setTab('js')}
        >
          JavaScript
        </StyledTab>
        <StyledTab
          type="button"
          $active={tab === 'py'}
          onClick={() => setTab('py')}
        >
          Python
        </StyledTab>
        <StyledTab
          type="button"
          $active={tab === 'rest'}
          onClick={() => setTab('rest')}
        >
          REST API
        </StyledTab>
      </StyledTabBar>
      <StyledCodeBlock>{codeSamples[tab]}</StyledCodeBlock>
      <StyledCardGrid>
        {cardData.map((card) => (
          <StyledDevCard key={card.title} $highlight={card.highlight}>
            <StyledCardIcon $color={card.highlight}>{card.icon}</StyledCardIcon>
            <StyledCardTitle>{card.title}</StyledCardTitle>
            <StyledCardPills>
              {card.pills.map((pill) => (
                <StyledCardPill key={pill}>{pill}</StyledCardPill>
              ))}
            </StyledCardPills>
          </StyledDevCard>
        ))}
      </StyledCardGrid>
    </AppPageSection>
  );
};

export default DeveloperSection;
