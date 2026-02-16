# WebSocket Integration Guide

## Overview

This guide documents the WebSocket integration patterns used in the Unpod platform for real-time communication, chat, and AI agent interactions.

## Architecture

### Technology Stack

- **WebSocket Library**: `react-use-websocket` v4.x
- **Real-time Voice**: LiveKit SDK
- **Connection Management**: Custom `useAgentConnection` hook
- **State Management**: React Context + useReducer

### Connection Flow

```
┌─────────────────┐
│  Component      │
│  Mount          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  useWebSocket   │◄────►│  Chat API        │
│  Hook           │      │  WebSocket       │
└────────┬────────┘      │  Server          │
         │               └──────────────────┘
         │
         ▼
┌─────────────────┐
│  Message        │
│  Processing     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  UI Update      │
└─────────────────┘
```

## WebSocket Implementation Pattern

### Basic Setup

```javascript
import useWebSocket from 'react-use-websocket';
import { useRef, useEffect } from 'react';

const MyComponent = () => {
  const didUnmount = useRef(false);

  // Authentication params
  const params = {
    token: userToken,
    app_type: process.env.appType,
  };

  // WebSocket connection
  const { sendJsonMessage, lastMessage } = useWebSocket(
    `${process.env.chatApiUrl}conversation/${conversationId}/`,
    {
      queryParams: params,
      shouldReconnect: (closeEvent) => {
        // Prevent reconnection after unmount
        return didUnmount.current === false;
      },
      reconnectAttempts: 10,
      reconnectInterval: 3000,
    }
  );

  useEffect(() => {
    return () => {
      didUnmount.current = true;
    };
  }, []);
};
```

### Key Configuration Options

| Option              | Type                      | Default     | Description                         |
|---------------------|---------------------------|-------------|-------------------------------------|
| `shouldReconnect`   | `(closeEvent) => boolean` | `true`      | Controls automatic reconnection     |
| `reconnectAttempts` | `number`                  | `10`        | Maximum reconnection attempts       |
| `reconnectInterval` | `number`                  | `3000` (ms) | Delay between reconnection attempts |
| `queryParams`       | `object`                  | `{}`        | Query parameters for WebSocket URL  |

## Connection Management

### useAgentConnection Hook

Located at: `libs/livekit/src/hooks/useAgentConnection.jsx`

This hook manages LiveKit room connections for voice agent interactions.

```javascript
import { useAgentConnection } from '@unpod/livekit/hooks/useAgentConnection';

const MyComponent = () => {
  const {
    wsUrl,           // LiveKit WebSocket URL
    roomToken,       // Room authentication token
    shouldConnect,   // Connection state flag
    connect,         // Connect to room
    disconnect,      // Disconnect from room
    updateRoomToken  // Update room token
  } = useAgentConnection();

  // Generate and set room token
  const startVoiceConnection = async () => {
    const response = await fetch('/api/generate-room-token');
    const { token } = await response.json();
    updateRoomToken(token);
    await connect('voice');
  };
};
```

### Provider Setup

Wrap your app with the `AgentConnectionProvider`:

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

## Message Handling

### Sending Messages

```javascript
// Send JSON message to WebSocket server
const sendMessage = () => {
  sendJsonMessage({
    event: 'action',
    data: {
      action: 'next',
      execution_type: 'chat',
      message: 'Hello, AI!'
    }
  });
};
```

### Receiving Messages

```javascript
import { useEffect } from 'react';

useEffect(() => {
  if (lastMessage !== null) {
    const data = JSON.parse(lastMessage.data);

    switch (data.event) {
      case 'message':
        handleNewMessage(data.payload);
        break;
      case 'typing':
        handleTypingIndicator(data.payload);
        break;
      case 'error':
        handleError(data.payload);
        break;
    }
  }
}, [lastMessage]);
```

## Common Patterns

### Pattern 1: Chat Conversation

Used in: `libs/modules/src/lib/AppPost/index.js`, `libs/modules/src/lib/AppThread/index.js`

```javascript
const ChatConversation = ({ conversationId, token }) => {
  const didUnmount = useRef(false);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  const { sendJsonMessage, lastMessage } = useWebSocket(
    `${process.env.chatApiUrl}conversation/${conversationId}/`,
    {
      queryParams: { token, app_type: process.env.appType },
      shouldReconnect: (closeEvent) => didUnmount.current === false,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
    }
  );

  // Handle incoming messages
  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      if (data.type === 'message') {
        setMessages(prev => [...prev, data.message]);
      }
    }
  }, [lastMessage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      didUnmount.current = true;
    };
  }, []);

  return (
    <div>
      {/* Chat UI */}
    </div>
  );
};
```

### Pattern 2: Voice Agent Integration

Used in: `libs/modules/src/lib/AppPost/index.js`

```javascript
const VoiceConversation = ({ postSlug }) => {
  const [conversationState, setConversationState] = useState('idle');
  const { roomToken, updateRoomToken } = useAgentConnection();

  // Generate room token when starting voice
  const onStartVoice = async () => {
    setConversationState('starting');

    try {
      const response = await getDataApi(
        `core/voice/${postSlug}/generate_room_token/`,
        { source: 'superkik' }
      );
      updateRoomToken(response.data.token);
    } catch (error) {
      console.error('Failed to generate room token:', error);
    }
  };

  return (
    <div>
      {roomToken && <VoiceAgentUI token={roomToken}/>}
    </div>
  );
};
```

### Pattern 3: Authenticated vs Anonymous

```javascript
const ConversationSetup = () => {
  const { isAuthenticated, visitorId, token } = useAuthContext();

  // Dynamic params based on authentication
  const params = isAuthenticated
    ? { token, app_type: process.env.appType }
    : { session_user: visitorId, app_type: process.env.appType };

  const { sendJsonMessage, lastMessage } = useWebSocket(
    websocketUrl,
    { queryParams: params, ...otherOptions }
  );
};
```

## Best Practices

### 1. Always Use didUnmount Pattern

**Why**: Prevents memory leaks and unwanted reconnections after component unmounts.

```javascript
const didUnmount = useRef(false);

const { sendJsonMessage } = useWebSocket(url, {
  shouldReconnect: () => didUnmount.current === false
});

useEffect(() => {
  return () => {
    didUnmount.current = true;
  };
}, []);
```

### 2. Handle Reconnection Logic

```javascript
const [reconnectAttempt, setReconnectAttempt] = useState(0);

const { sendJsonMessage } = useWebSocket(url, {
  shouldReconnect: (closeEvent) => {
    // Don't reconnect if intentionally closed
    if (closeEvent.code === 1000) return false;

    // Don't reconnect if unmounted
    if (didUnmount.current) return false;

    // Track reconnection attempts
    setReconnectAttempt(prev => prev + 1);
    return reconnectAttempt < 10;
  },
  reconnectInterval: (attemptNumber) => {
    // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
    return Math.min(1000 * Math.pow(2, attemptNumber), 30000);
  }
});
```

### 3. Parse Messages Safely

```javascript
useEffect(() => {
  if (!lastMessage) return;

  try {
    const data = JSON.parse(lastMessage.data);
    handleMessage(data);
  } catch (error) {
    console.error('Failed to parse WebSocket message:', error);
  }
}, [lastMessage]);
```

### 4. Debounce Frequent Operations

```javascript
import { useCallback } from 'react';
import debounce from 'lodash/debounce';

const debouncedSend = useCallback(
  debounce((message) => {
    sendJsonMessage(message);
  }, 300),
  [sendJsonMessage]
);
```

### 5. Handle Connection States

```javascript
const [connectionStatus, setConnectionStatus] = useState('connecting');

const { sendJsonMessage, readyState } = useWebSocket(url, {
  onOpen: () => setConnectionStatus('connected'),
  onClose: () => setConnectionStatus('disconnected'),
  onError: () => setConnectionStatus('error'),
});

// ReadyState values:
// 0 - CONNECTING
// 1 - OPEN
// 2 - CLOSING
// 3 - CLOSED
```

## Environment Variables

Required environment variables for WebSocket connections:

```bash
# Chat WebSocket API
chatApiUrl=wss://qa1-block-service.unpod.tv/ws/v1/

# LiveKit WebSocket URL (for voice)
NEXT_PUBLIC_LIVEKIT_URL=wss://your-livekit-server.com

# Application type
appType=social

# Product ID
productId=unpod.ai
```

## Troubleshooting

### Issue: WebSocket Keeps Reconnecting After Unmount

**Solution**: Ensure `didUnmount` pattern is implemented correctly:

```javascript
const didUnmount = useRef(false);

useEffect(() => {
  return () => {
    didUnmount.current = true;
  };
}, []);
```

### Issue: Messages Not Received

**Checklist**:

1. ✅ WebSocket connection is open (`readyState === 1`)
2. ✅ Query params include valid authentication
3. ✅ Server is sending messages in correct format
4. ✅ `lastMessage` dependency is in useEffect

```javascript
// Debug WebSocket state
console.log('ReadyState:', readyState);
console.log('Last Message:', lastMessage);
```

### Issue: Connection Fails with 401

**Solution**: Check authentication params:

```javascript
const params = {
  token: userToken, // Ensure this is valid
  app_type: process.env.appType
};
```

### Issue: Excessive Reconnections

**Solution**: Implement exponential backoff:

```javascript
const { sendJsonMessage } = useWebSocket(url, {
  reconnectInterval: (attemptNumber) => {
    return Math.min(1000 * Math.pow(2, attemptNumber), 30000);
  },
  reconnectAttempts: 10
});
```

## Performance Considerations

### 1. Message Batching

For high-frequency updates, batch messages:

```javascript
const messageQueue = useRef([]);
const flushInterval = useRef(null);

const queueMessage = (message) => {
  messageQueue.current.push(message);

  if (!flushInterval.current) {
    flushInterval.current = setInterval(() => {
      if (messageQueue.current.length > 0) {
        sendJsonMessage({
          batch: messageQueue.current
        });
        messageQueue.current = [];
      }
    }, 100);
  }
};
```

### 2. Memoize Message Handlers

```javascript
const handleMessage = useCallback((data) => {
  // Process message
}, [/* dependencies */]);

useEffect(() => {
  if (lastMessage) {
    const data = JSON.parse(lastMessage.data);
    handleMessage(data);
  }
}, [lastMessage, handleMessage]);
```

### 3. Cleanup Resources

```javascript
useEffect(() => {
  return () => {
    didUnmount.current = true;
    // Clear any intervals
    clearInterval(flushInterval.current);
    // Cancel pending requests
    // Clean up subscriptions
  };
}, []);
```

## Testing

### Mock WebSocket Connection

```javascript
import { renderHook } from '@testing-library/react-hooks';
import useWebSocket from 'react-use-websocket';

jest.mock('react-use-websocket');

test('handles WebSocket messages', () => {
  const mockSendJsonMessage = jest.fn();
  const mockLastMessage = { data: JSON.stringify({ type: 'test' }) };

  useWebSocket.mockReturnValue({
    sendJsonMessage: mockSendJsonMessage,
    lastMessage: mockLastMessage,
    readyState: 1
  });

  // Your test code
});
```

## Related Documentation

- [LiveKit Documentation](https://docs.livekit.io/)
- [react-use-websocket](https://github.com/robtaussig/react-use-websocket)
- [WebSocket API MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## Support

For issues or questions:

- Check existing patterns in `libs/modules/src/lib/AppPost/index.js`
- Review LiveKit hooks in `libs/livekit/src/hooks/`
- Consult team documentation

---

**Last Updated**: 2025-12-30
**Version**: 1.0.0
