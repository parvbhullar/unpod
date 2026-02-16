# LiveKit Text Streams Guide

## Overview

The `useConversationDataChannel` hook uses **LiveKit Text Streams API** for real-time messaging in conversations. This is the official, high-level API for text communication in LiveKit.

## How It Works

### LiveKit Text Streams

- **API**: `room.localParticipant.sendText()` and `room.registerTextStreamHandler()`
- **Requirements**: Active LiveKit room connection
- **Modes**: Works with voice/video OR data-only connections
- **Benefits**:
  - Official LiveKit API (not low-level data packets)
  - Automatic message chunking (no size limits)
  - Topic-based routing
  - Low latency
  - Supports concurrent streams
  - Clean async/await interface

## Usage

### Basic Example

```javascript
import { useConversationDataChannel } from '@unpod/livekit';
import { LiveKitRoom } from '@livekit/components-react';

const MyComponent = () => {
  const { sendJsonMessage, lastMessage, isConnected } = useConversationDataChannel({
    conversationId: 'conversation-123',
    params: {
      token: 'user-token',
      app_type: 'social'
    },
    enabled: true,
    topic: 'chat' // Optional, defaults to 'chat'
  });

  const handleSendMessage = async () => {
    await sendJsonMessage({
      event: 'message',
      content: 'Hello world!',
      type: 'text'
    });
  };

  return (
    <LiveKitRoom
      token={livekitToken}
      serverUrl="wss://your-livekit-server.com"
    >
      <div>
        <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
        <button onClick={handleSendMessage}>Send Message</button>
      </div>
    </LiveKitRoom>
  );
};
```

### Data-Only Mode (Text Without Voice)

LiveKit supports connecting to a room without publishing audio/video tracks:

```javascript
import { useRoomContext } from '@livekit/components-react';

// In your component
const room = useRoomContext();

// Connect to room without audio/video
await room.connect(url, token, {
  autoSubscribe: false, // Don't auto-subscribe to others' tracks
  // Don't publish audio/video tracks - data-only mode
});

// Now you can use text streams without voice!
```

## API Reference

### Hook Parameters

```typescript
{
  conversationId ? : string;    // Optional conversation ID for metadata
  params ? : object;            // Additional parameters to include in messages
  enabled ? : boolean;          // Enable/disable messaging (default: true)
  topic ? : string;            // Message topic for routing (default: 'chat')
}
```

### Hook Return Values

```typescript
{
  sendJsonMessage: (data: object) => Promise<void>;  // Send a message
  lastMessage: {                                      // Last received message
    data: string;                                     // JSON string
    timestamp: number;                                // Unix timestamp
    participant ? : ParticipantInfo;                    // Sender info
    source: 'transcription' | 'livekit';             // Message source
  }
|
  null;
  isConnected: boolean;                              // LiveKit connection state
  agentTranscription: object;                        // Voice agent transcription
  localTranscription: object;                        // Local user transcription
  voiceAssistant: object;                            // Voice assistant instance
}
```

## Features

### 1. Topic-Based Routing

Messages use topics for organization:

```javascript
// Send to 'chat' topic (default)
await sendJsonMessage({ content: 'Hello' });

// Send to custom topic
const hook = useConversationDataChannel({ topic: 'notifications' });
await hook.sendJsonMessage({ type: 'notification', text: 'New message' });
```

### 2. Automatic Chunking

LiveKit automatically handles large messages:

```javascript
// No size limit - automatically chunked
await sendJsonMessage({
  content: veryLongString,
  attachments: [largeDataObject]
});
```

### 3. Voice Transcriptions

The hook automatically captures voice-to-text:

```javascript
const { lastMessage } = useConversationDataChannel({ ... });

useEffect(() => {
  if (lastMessage?.source === 'transcription') {
    const data = JSON.parse(lastMessage.data);
    console.log('Voice message:', data.text);
    console.log('Is final?', data.final);
  }
}, [lastMessage]);
```

### 4. Concurrent Streams

Multiple messages can be sent/received simultaneously:

```javascript
// Both will be handled concurrently
await Promise.all([
  sendJsonMessage({ type: 'message', content: 'First' }),
  sendJsonMessage({ type: 'message', content: 'Second' })
]);
```

## Message Flow

### Sending Messages

```
Component calls sendJsonMessage()
  ↓
Check if enabled and connected
  ↓
Prepare JSON payload
  ↓
room.localParticipant.sendText(json, { topic })
  ↓
LiveKit handles chunking and transmission
  ↓
Other participants receive via registered handler
```

### Receiving Messages

```
Participant sends text stream
  ↓
room.registerTextStreamHandler() triggered
  ↓
reader.readAll() gets complete message
  ↓
Parse JSON and update lastMessage state
  ↓
Component receives update via lastMessage
```

## Best Practices

### 1. Always Wrap in LiveKitRoom

```javascript
<LiveKitRoom token={token} serverUrl={serverUrl}>
  <YourComponent/>
  {/* Uses useConversationDataChannel */}
</LiveKitRoom>
```

### 2. Handle Connection State

```javascript
const { isConnected, sendJsonMessage } = useConversationDataChannel({ ... });

const handleSend = async () => {
  if (!isConnected) {
    console.warn('Not connected yet');
    return;
  }
  await sendJsonMessage(data);
};
```

### 3. Parse Received Messages

```javascript
useEffect(() => {
  if (!lastMessage) return;

  try {
    const data = JSON.parse(lastMessage.data);
    // Handle message based on type or source
    if (lastMessage.source === 'livekit') {
      // Text message from another participant
    } else if (lastMessage.source === 'transcription') {
      // Voice-to-text transcription
    }
  } catch (error) {
    console.error('Failed to parse message:', error);
  }
}, [lastMessage]);
```

### 4. Clean Topic Names

```javascript
// Good - descriptive, lowercase, no spaces
topic: 'chat'
topic: 'notifications'
topic: 'system-events'

// Avoid - generic or unclear
topic: 'messages'
topic: 'data'
```

## Troubleshooting

### Messages Not Sending

**Check console logs:**

```
Cannot send message: LiveKit room not connected
```

**Solutions:**

- Ensure LiveKitRoom is connected
- Check `isConnected` state before sending
- Verify LiveKit token is valid
- Check room connection logs

### Messages Not Receiving

**Check console logs:**

```
Registering LiveKit text stream handler for topic: chat
```

**Solutions:**

- Verify both participants are using the same topic
- Check that text stream handler registered successfully
- Ensure receiver joined before message was sent (LiveKit is real-time only)
- Check for JavaScript errors in console

### Connection Issues

```
useConversationDataChannel: no room context
❌ LiveKit disconnected
```

**Solutions:**

- Wrap component in `<LiveKitRoom>` provider
- Ensure LiveKit token generation is working
- Check network connectivity
- Verify LiveKit server URL is correct

## Advanced Usage

### Incremental Reading (Streaming)

For large messages or LLM-style streaming:

```javascript
// Instead of reader.readAll(), process chunks:
room.registerTextStreamHandler('chat', async (reader, participantInfo) => {
  for await (const chunk of reader) {
    console.log('Next chunk:', chunk);
    // Update UI incrementally
  }
});
```

### Custom Metadata

```javascript
await sendJsonMessage({
  content: 'Hello',
  metadata: {
    timestamp: Date.now(),
    userId: currentUser.id,
    threadId: 'thread-123'
  }
});
```

### Multiple Topics

```javascript
// Chat messages
const chatHook = useConversationDataChannel({ topic: 'chat' });

// System notifications
const notificationHook = useConversationDataChannel({ topic: 'notifications' });

// Use them independently
await chatHook.sendJsonMessage({ message: 'Hi!' });
await notificationHook.sendJsonMessage({ alert: 'New update' });
```

## Environment Configuration

LiveKit server URL should be configured in your environment:

```javascript
// In LiveKitRoom component
<LiveKitRoom
  token={livekitToken}
  serverUrl={process.env.LIVEKIT_SERVER_URL || 'wss://your-server.com'}
>
```

## Migration from WebSocket

If migrating from WebSocket-based messaging:

**Before (WebSocket):**

```javascript
const { sendJsonMessage } = useWebSocket(url);
sendJsonMessage({ message: 'Hello' }); // Synchronous
```

**After (LiveKit):**

```javascript
const { sendJsonMessage } = useConversationDataChannel({ ... });
await sendJsonMessage({ message: 'Hello' }); // Async
```

**Key differences:**

- LiveKit requires room connection
- `sendJsonMessage` is now async (returns Promise)
- Messages are topic-based
- Built-in support for voice transcriptions

## Technical Details

### Dependencies

- `@livekit/components-react`: Latest
- `livekit-client`: Latest (Text Streams API)

### API Methods Used

- `room.localParticipant.sendText()` - Send messages
- `room.registerTextStreamHandler()` - Receive messages
- `room.on('connectionStateChanged')` - Track connection

### File Location

`libs/livekit/src/hooks/useConversationDataChannel.jsx`

### References

- [LiveKit Text Streams Documentation](https://docs.livekit.io/transport/data/text-streams/)
- [LiveKit Room API](https://docs.livekit.io/client-sdk-js/classes/Room.html)
- [LiveKit Components React](https://docs.livekit.io/client-sdk-js/classes/LiveKitRoom.html)

## Support

For LiveKit-specific issues:

- [LiveKit Discord Community](https://livekit.io/discord)
- [LiveKit GitHub Issues](https://github.com/livekit/livekit/issues)

For implementation questions:

- Check console logs for detailed error messages
- Verify LiveKit room connection state
- Review this guide's troubleshooting section
