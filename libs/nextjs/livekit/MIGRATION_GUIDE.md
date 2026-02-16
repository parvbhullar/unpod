# Migration Guide: WebSocket to LiveKit Events

This guide explains the migration from `react-use-websocket` to LiveKit's data channel events for real-time communication.

## Overview

**Before**: WebSocket connections using `react-use-websocket`
**After**: LiveKit data channel using `useLiveKitEvents` hook

### Benefits of LiveKit Events

✅ **Unified Communication**: Voice + messaging in single connection
✅ **Better Performance**: Native WebRTC data channels
✅ **Reliable Delivery**: Built-in reliability options
✅ **Room-based**: Scoped to LiveKit rooms automatically
✅ **Type Safety**: Structured message handling

## Migration Steps

### 1. Replace WebSocket Hook

**Before:**

```javascript
import useWebSocket from 'react-use-websocket';

const { sendJsonMessage, lastMessage } = useWebSocket(
  `${process.env.chatApiUrl}conversation/${conversationId}/`,
  {
    queryParams: params,
    shouldReconnect: () => didUnmount.current === false,
    reconnectAttempts: 10,
    reconnectInterval: 3000,
  }
);
```

**After:**

```javascript
import { useLiveKitEvents } from '@unpod/livekit/hooks/useLiveKitEvents';

const { sendJsonMessage, lastMessage } = useLiveKitEvents(
  conversationId,
  {
    queryParams: params,
    enabled: didUnmount.current === false,
  }
);
```

### 2. Update Imports

**Before:**

```javascript
import useWebSocket from 'react-use-websocket';
```

**After:**

```javascript
import { useLiveKitEvents } from '@unpod/livekit/hooks/useLiveKitEvents';
// OR
import { useLiveKitEvents } from '@unpod/livekit/hooks';
```

### 3. Ensure LiveKit Room Context

The `useLiveKitEvents` hook requires a LiveKit room context. Ensure your component is wrapped with LiveKit's `LiveKitRoom`.

**Implementation in parent component (e.g., ThreadModule):**

```javascript
import { useEffect, useState } from 'react';
import { LiveKitRoom } from '@livekit/components-react';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';

function ThreadModule({ post }) {
  const [roomToken, setRoomToken] = useState(null);
  const [isLoadingToken, setIsLoadingToken] = useState(true);
  const infoViewActionsContext = useInfoViewActionsContext();

  // Generate LiveKit room token for conversation messaging
  useEffect(() => {
    if (post?.parent_post_slug || post?.slug) {
      const slug = post.parent_post_slug || post.slug;

      getDataApi(
        `core/voice/${slug}/generate_room_token/`,
        infoViewActionsContext,
        { source: 'conversation' }
      )
        .then(({ data }) => {
          setRoomToken(data.token);
          setIsLoadingToken(false);
        })
        .catch((error) => {
          console.error('Failed to generate room token:', error);
          setIsLoadingToken(false);
        });
    }
  }, [post?.slug]);

  return isLoadingToken ? (
    <Spin/>
  ) : roomToken ? (
    <LiveKitRoom
      serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
      token={roomToken}
      connect={true}
    >
      <YourComponent/>
    </LiveKitRoom>
  ) : (
    <YourComponent/>
  {/* Fallback without LiveKit */
  }
)
  ;
}
```

## API Changes

### Hook Parameters

#### WebSocket (Old)

```javascript
useWebSocket(url, options)
```

**Parameters:**

- `url`: WebSocket URL string
- `options.queryParams`: Query parameters
- `options.shouldReconnect`: Reconnection logic function
- `options.reconnectAttempts`: Number of attempts
- `options.reconnectInterval`: Delay between attempts

#### LiveKit Events (New)

```javascript
useLiveKitEvents(conversationId, options)
```

**Parameters:**

- `conversationId`: Conversation identifier
- `options.queryParams`: Authentication and metadata params
- `options.enabled`: Whether connection is enabled (replaces `shouldReconnect`)

### Return Values

Both hooks return the same interface:

```javascript
{
  sendJsonMessage: (data) => void,  // Send JSON message
    lastMessage
:
  {                     // Last received message
    data: string,                    // Message data (JSON string)
      timeStamp
  :
    number,               // Message timestamp
      origin
  :
    string                   // Sender identity
  }
,
  readyState: number,                // Connection state (0-3)
    isConnected
:
  boolean               // Helper for readyState === 1
}
```

## Message Handling

### Sending Messages

No changes required - same API:

```javascript
sendJsonMessage({
  event: 'block',
  pilot: 'ai-agent',
  data: {
    content: 'Hello!',
    block_type: 'text_msg'
  }
});
```

### Receiving Messages

No changes required - same pattern:

```javascript
useEffect(() => {
  if (lastMessage) {
    const data = JSON.parse(lastMessage.data);
    console.log('Received:', data);
  }
}, [lastMessage]);
```

## Complete Example

### Before (WebSocket)

```javascript
import React, { useRef, useEffect } from 'react';
import useWebSocket from 'react-use-websocket';

function ChatComponent({ conversationId, token }) {
  const didUnmount = useRef(false);

  const { sendJsonMessage, lastMessage } = useWebSocket(
    `${process.env.chatApiUrl}conversation/${conversationId}/`,
    {
      queryParams: { token, app_type: process.env.appType },
      shouldReconnect: () => didUnmount.current === false,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
    }
  );

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      handleMessage(data);
    }
  }, [lastMessage]);

  useEffect(() => {
    return () => {
      didUnmount.current = true;
    };
  }, []);

  return <div>{/* UI */}</div>;
}
```

### After (LiveKit Events)

```javascript
import React, { useRef, useEffect } from 'react';
import { useLiveKitEvents } from '@unpod/livekit/hooks/useLiveKitEvents';
import { LiveKitRoom } from '@livekit/components-react';

function ChatComponent({ conversationId, token, roomToken }) {
  const didUnmount = useRef(false);

  const { sendJsonMessage, lastMessage } = useLiveKitEvents(
    conversationId,
    {
      queryParams: { token, app_type: process.env.appType },
      enabled: didUnmount.current === false,
    }
  );

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      handleMessage(data);
    }
  }, [lastMessage]);

  useEffect(() => {
    return () => {
      didUnmount.current = true;
    };
  }, []);

  return <div>{/* UI */}</div>;
}

// Wrap with LiveKitRoom
function ChatWithRoom({ conversationId, token, roomToken }) {
  return (
    <LiveKitRoom
      serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
      token={roomToken}
      connect={true}
    >
      <ChatComponent
        conversationId={conversationId}
        token={token}
        roomToken={roomToken}
      />
    </LiveKitRoom>
  );
}
```

## Files Updated

### 1. Created Hook

- **File**: `libs/livekit/src/hooks/useLiveKitEvents.jsx`
- **Purpose**: LiveKit-based WebSocket replacement
- **Features**:
  - Data channel subscription
  - JSON message encoding/decoding
  - Connection state management
  - Automatic cleanup

### 2. Updated Components

- **File**: `libs/modules/src/lib/AppPost/index.js`
- **Changes**:
  - Replaced `useWebSocket` with `useLiveKitEvents`
  - Updated import statements
  - Maintained same interface for child components

### 3. Hook Exports

- **File**: `libs/livekit/src/hooks/index.js`
- **Purpose**: Centralized exports for livekit hooks

## Troubleshooting

### Issue: "Cannot read properties of undefined (reading 'publishData')"

**Cause**: Component not wrapped in LiveKit room context

**Solution**:

```javascript
<LiveKitRoom ...>
<
YourComponent / >
< /LiveKitRoom>
```

### Issue: Messages not being received

**Checklist**:

1. ✅ Room is connected (`room.state === 'connected'`)
2. ✅ Data channel topic matches ('conversation')
3. ✅ Local participant exists
4. ✅ Component has `lastMessage` in useEffect dependencies

**Debug**:

```javascript
const { readyState, isConnected } = useLiveKitEvents(...);
console.log('Ready State:', readyState); // Should be 1
console.log('Is Connected:', isConnected); // Should be true
```

### Issue: Messages sent but not received by server

**Possible Causes**:

- Server not subscribed to LiveKit data channel
- Topic mismatch
- Encoding issues

**Solution**: Ensure server is listening to the same data channel topic:

```javascript
// Client sends on topic 'conversation'
localParticipant.publishData(encodedData, {
  topic: 'conversation',
});

// Server must listen to topic 'conversation'
room.on('dataReceived', (payload, participant, kind, topic) => {
  if (topic === 'conversation') {
    // Handle message
  }
});
```

## Testing

### Mock LiveKit Events

```javascript
import { useLiveKitEvents } from '@unpod/livekit/hooks/useLiveKitEvents';

jest.mock('@unpod/livekit/hooks/useLiveKitEvents');

beforeEach(() => {
  useLiveKitEvents.mockReturnValue({
    sendJsonMessage: jest.fn(),
    lastMessage: null,
    readyState: 1,
    isConnected: true
  });
});

test('sends message', () => {
  const { sendJsonMessage } = useLiveKitEvents();
  sendJsonMessage({ event: 'test' });
  expect(sendJsonMessage).toHaveBeenCalledWith({ event: 'test' });
});
```

## Performance Considerations

### Before (WebSocket)

- Separate connection for chat
- HTTP polling fallback
- Limited to text data

### After (LiveKit Events)

- Reuses existing LiveKit connection
- Native WebRTC data channels
- Supports binary and text data
- Lower latency

## Rollback Plan

If needed, reverting is straightforward:

1. Change import back to `useWebSocket`
2. Restore URL parameter (instead of conversationId)
3. Update options (replace `enabled` with `shouldReconnect` function)

## Next Steps

1. ✅ Test message sending/receiving
2. ✅ Verify cleanup on unmount
3. ✅ Monitor connection stability
4. ✅ Update other components using WebSocket
5. ⬜ Remove `react-use-websocket` dependency (once all components migrated)

## Support

For questions or issues:

- Check [WEBSOCKET_GUIDE.md](./WEBSOCKET_GUIDE.md)
- Review [LiveKit Data Channels](https://docs.livekit.io/realtime/client/data-messages/)
- Consult team documentation

---

**Migration Date**: 2025-12-30
**Status**: ✅ Complete for AppPost component
**Next**: Migrate AppThread and other WebSocket usages
