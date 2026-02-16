# @unpod/livekit

Real-time communication library for Unpod platform, providing WebSocket integration, voice agent connections, and LiveKit SDK components.

## Overview

This library provides:

- **WebSocket Communication**: Real-time chat and messaging via `react-use-websocket`
- **Voice Agent Integration**: LiveKit-powered voice conversations with AI agents
- **Connection Management**: Custom hooks for managing real-time connections
- **UI Components**: Ready-to-use chat, voice, and visualization components

## Installation

This library is part of the Nx monorepo and is imported as:

```javascript
import { useAgentConnection } from '@unpod/livekit/hooks/useAgentConnection';
import AppVoiceAgent from '@unpod/livekit/AppVoiceAgent';
```

## Quick Start

### 1. Setup Provider

Wrap your application with the AgentConnectionProvider:

```javascript
import { AgentConnectionProvider } from '@unpod/livekit/hooks/useAgentConnection';

function App({ children }) {
  return (
    <AgentConnectionProvider>
      {children}
    </AgentConnectionProvider>
  );
}
```

### 2. Use LiveKit Data Channel for Conversations (Recommended)

**NEW:** Instead of using separate WebSocket connections, use LiveKit's data channel for conversation messages:

```javascript
import { LiveKitRoom } from '@livekit/components-react';
import { useConversationDataChannel } from '@unpod/livekit/hooks/useConversationDataChannel';
import { useAgentConnection } from '@unpod/livekit/hooks/useAgentConnection';

function ChatComponent({ conversationId, token }) {
  const { wsUrl, roomToken, shouldConnect } = useAgentConnection();

  return (
    <LiveKitRoom serverUrl={wsUrl} token={roomToken} connect={shouldConnect}>
      <ConversationContent conversationId={conversationId} token={token}/>
    </LiveKitRoom>
  );
}

function ConversationContent({ conversationId, token }) {
  const params = {
    token,
    app_type: process.env.appType,
  };

  const { sendJsonMessage, lastMessage, isConnected } = useConversationDataChannel({
    conversationId,
    params,
    enabled: true,
  });

  // Handle messages
  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      console.log('Received:', data);
    }
  }, [lastMessage]);

  return <div>{/* Your UI */}</div>;
}
```

**Benefits:**

- Single connection for both voice and chat
- Automatic reconnection handled by LiveKit
- Better connection management
- Reduced overhead from multiple WebSocket connections

### 3. Voice Agent Integration

```javascript
import { useAgentConnection } from '@unpod/livekit/hooks/useAgentConnection';
import AppVoiceAgent from '@unpod/livekit/AppVoiceAgent';

function VoiceChat({ agentId }) {
  const { roomToken, updateRoomToken } = useAgentConnection();

  const startVoiceCall = async () => {
    const response = await fetch('/api/generate-room-token', {
      method: 'POST',
      body: JSON.stringify({ agentId })
    });
    const { token } = await response.json();
    updateRoomToken(token);
  };

  return (
    <div>
      {!roomToken ? (
        <button onClick={startVoiceCall}>Start Voice Call</button>
      ) : (
        <AppVoiceAgent
          spaceToken={spaceToken}
          agentId={agentId}
          agentName="AI Assistant"
          name="User Name"
          email="user@example.com"
        />
      )}
    </div>
  );
}
```

## Library Structure

```
libs/livekit/
├── src/
│   ├── hooks/
│   │   ├── useAgentConnection.jsx         # LiveKit room connection management
│   │   ├── useConversationDataChannel.jsx # Conversation messaging via LiveKit data channel
│   │   ├── useConnection.jsx              # Generic connection hook
│   │   ├── useConfig.jsx                  # Audio/video configuration
│   │   ├── useTrackVolume.jsx             # Audio volume monitoring
│   │   └── useWindowResize.jsx            # Responsive UI handling
│   │
│   ├── AppVoiceAgent/
│   │   ├── index.js                  # Main voice agent component
│   │   ├── AgentView.jsx             # Agent UI container
│   │   ├── VoiceAgent.jsx            # Voice interaction UI
│   │   ├── ChatWidget.jsx            # Chat interface
│   │   └── config/                   # Audio configuration components
│   │       ├── AudioInputTile.jsx
│   │       ├── AudioOutputTile.jsx
│   │       ├── CircularVisualizer.jsx
│   │       └── BarVisualizer.jsx
│   │
│   ├── components/
│   │   ├── chat/                     # Chat UI components
│   │   │   ├── ChatTile.jsx
│   │   │   ├── ChatMessage.jsx
│   │   │   └── ChatMessageInput.jsx
│   │   ├── config/                   # Configuration components
│   │   │   ├── AudioInputTile.jsx
│   │   │   ├── AudioOutputTile.jsx
│   │   │   └── CircularVisualizer.js
│   │   └── playground/               # Testing/demo components
│   │       ├── Playground.jsx
│   │       └── PlaygroundTile.jsx
│   │
│   └── transcriptions/
│       └── TranscriptionTile.jsx     # Real-time transcription display
│
├── WEBSOCKET_GUIDE.md                # Detailed WebSocket documentation
└── README.md                         # This file
```

## Key Components

### useConversationDataChannel

**NEW:** Manages conversation messaging via LiveKit's data channel. Replaces WebSocket for chat messages.

```javascript
const {
  sendJsonMessage, // Send JSON messages via data channel
  lastMessage,     // Last received message (same format as WebSocket)
  isConnected      // Connection status
} = useConversationDataChannel({
  conversationId: 'post-123',
  params: { token: 'user-token', app_type: 'social' },
  enabled: true
});
```

**Features:**

- Compatible API with `react-use-websocket`
- Automatic reconnection via LiveKit
- Uses 'conversation' topic for message routing
- Handles message encoding/decoding automatically

### useAgentConnection

Manages LiveKit room connections for voice agents.

```javascript
const {
  wsUrl,           // WebSocket URL for LiveKit
  roomToken,       // Authentication token
  shouldConnect,   // Connection state
  connect,         // Connect to room
  disconnect,      // Disconnect from room
  updateRoomToken  // Update authentication token
} = useAgentConnection();
```

### AppVoiceAgent

Complete voice agent UI with audio controls and chat.

```javascript
<AppVoiceAgent
  spaceToken={string}      // Space authentication token
  agentId={string}         // Agent identifier
  agentName={string}       // Display name
  name={string}            // User name
  email={string}           // User email
  contactName={string}     // Contact name (optional)
/>
```

### ChatWidget

Standalone chat interface component.

```javascript
<ChatWidget
  messages={Array}         // Chat messages
  onSendMessage={Function} // Message send handler
  isTyping={boolean}       // Typing indicator
/>
```

## WebSocket Patterns

### Basic Pattern

```javascript
const didUnmount = useRef(false);

const { sendJsonMessage, lastMessage } = useWebSocket(url, {
  queryParams: authParams,
  shouldReconnect: () => didUnmount.current === false,
  reconnectAttempts: 10,
  reconnectInterval: 3000,
});

useEffect(() => {
  return () => {
    didUnmount.current = true;
  };
}, []);
```

### With Authentication

```javascript
const { isAuthenticated, visitorId, token } = useAuthContext();

const params = isAuthenticated
  ? { token, app_type: process.env.appType }
  : { session_user: visitorId, app_type: process.env.appType };

const { sendJsonMessage } = useWebSocket(url, {
  queryParams: params,
  // ... other options
});
```

## Environment Variables

Required environment variables:

```bash
# Chat WebSocket API
chatApiUrl=wss://qa1-block-service.unpod.tv/ws/v1/

# LiveKit server URL
NEXT_PUBLIC_LIVEKIT_URL=wss://your-livekit-server.com

# Application configuration
appType=social
productId=unpod.ai
```

## Documentation

- **[WebSocket Guide](./WEBSOCKET_GUIDE.md)** - Comprehensive WebSocket integration patterns
- **[LiveKit Docs](https://docs.livekit.io/)** - Official LiveKit documentation
- **[react-use-websocket](https://github.com/robtaussig/react-use-websocket)** - WebSocket library

## Examples

### Real-world Usage

1. **AppPost** (`libs/modules/src/lib/AppPost/index.js`)

- Chat conversation with AI
- Voice agent integration
- Real-time message streaming

2. **AppThread** (`libs/modules/src/lib/AppThread/index.js`)

- Thread-based conversations
- Reply management
- Message persistence

## Best Practices

1. **Always implement didUnmount pattern** to prevent memory leaks
2. **Use exponential backoff** for reconnection attempts
3. **Parse messages safely** with try-catch
4. **Handle connection states** (connecting, connected, disconnected)
5. **Cleanup resources** in useEffect cleanup function

## Common Issues

### WebSocket Won't Connect

```javascript
// Check authentication params
console.log('Query Params:', queryParams);
console.log('WebSocket URL:', websocketUrl);
console.log('Ready State:', readyState);
```

### Component Keeps Reconnecting

```javascript
// Ensure didUnmount is set on cleanup
useEffect(() => {
  return () => {
    didUnmount.current = true;
  };
}, []);
```

### Messages Not Received

```javascript
// Verify lastMessage dependency
useEffect(() => {
  if (lastMessage) {
    console.log('Message:', lastMessage);
  }
}, [lastMessage]); // Must include lastMessage!
```

## Testing

### Mock WebSocket

```javascript
import useWebSocket from 'react-use-websocket';

jest.mock('react-use-websocket');

beforeEach(() => {
  useWebSocket.mockReturnValue({
    sendJsonMessage: jest.fn(),
    lastMessage: null,
    readyState: 1
  });
});
```

## Performance

- Messages are processed in real-time
- Connection pooling for multiple conversations
- Automatic reconnection with exponential backoff
- Optimized rendering with React.memo

## Contributing

When adding new features:

1. Follow existing patterns in `WEBSOCKET_GUIDE.md`
2. Add TypeScript types for new hooks
3. Include usage examples
4. Update documentation

## Running Tests

```bash
# Run all tests
nx test livekit

# Run specific test
nx test livekit --testFile=useAgentConnection.spec.js
```

## Support

For questions or issues:

- Review [WEBSOCKET_GUIDE.md](./WEBSOCKET_GUIDE.md) for detailed patterns
- Check existing implementations in `libs/modules/src/lib/`
- Consult team documentation

---

**Generated with**: [Nx](https://nx.dev)
**Last Updated**: 2025-12-30
**Version**: 1.0.0
