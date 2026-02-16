/**
 * Test script for Centrifugo connection
 * Run with: node scripts/test-centrifugo.mjs
 */

import { Centrifuge } from 'centrifuge';

// Test configuration from user
const config = {
  token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzOCIsImV4cCI6MTc2OTc5MzUzNCwiaW5mbyI6eyJlbWFpbCI6InBhcnZpbmRlcitodWJAcmVjYWxsbC5jbyJ9fQ.7zmhmCLOvtCf-Shpsf-lMMdGYHwIdefm5EFNH2FHX10",
  channel_name: "session:no-title-675154650055311617-F1O3QJM1Y7Q1AVVUYNV4VPRB-1769789934028",
  agent_name: "superkik-qa-assistant-agent-v1",
  space_token: "F1O3QJM1Y7Q1AVVUYNV4VPRB",
};

// Centrifugo WebSocket URLs to try
const wsUrls = [
  'wss://qa1.unpod.tv/connection/websocket',
  'wss://qa1.unpod.tv/centrifugo/connection/websocket',
  'wss://qa1-block-service.unpod.tv/centrifugo/connection/websocket',
];

// Try the first URL (you can change the index to test others)
const wsUrl = wsUrls[0];

console.log('🔌 Testing Centrifugo Connection');
console.log('================================');
console.log('URL:', wsUrl);
console.log('Channel:', config.channel_name);
console.log('');

// Create Centrifuge client
const centrifuge = new Centrifuge(wsUrl, {
  token: config.token,
});

// Connection state handlers
centrifuge.on('connecting', (ctx) => {
  console.log('⏳ Connecting...', ctx);
});

centrifuge.on('connected', (ctx) => {
  console.log('✅ Connected!', ctx);
  console.log('');

  // Now subscribe to the channel
  subscribeToChannel();
});

centrifuge.on('disconnected', (ctx) => {
  console.log('❌ Disconnected:', ctx);
});

centrifuge.on('error', (ctx) => {
  console.error('🚨 Error:', ctx);
});

// Subscribe to channel
function subscribeToChannel() {
  console.log('📡 Subscribing to channel:', config.channel_name);

  const subscription = centrifuge.newSubscription(config.channel_name);

  subscription.on('subscribing', (ctx) => {
    console.log('⏳ Subscribing...', ctx);
  });

  subscription.on('subscribed', (ctx) => {
    console.log('✅ Subscribed to channel!', ctx);
    console.log('');
    console.log('🎧 Listening for messages... (Press Ctrl+C to exit)');
    console.log('');

    // Try to publish a test message
    setTimeout(() => {
      console.log('📤 Sending test message...');
      subscription.publish({
        type: 'test',
        message: 'Hello from test script',
        timestamp: Date.now(),
        agent_name: config.agent_name,
        space_token: config.space_token,
      }).then(() => {
        console.log('✅ Test message sent successfully!');
      }).catch((err) => {
        console.log('⚠️ Could not publish (may need server-side publish):', err.message);
      });
    }, 1000);
  });

  subscription.on('unsubscribed', (ctx) => {
    console.log('📴 Unsubscribed:', ctx);
  });

  subscription.on('error', (ctx) => {
    console.error('🚨 Subscription error:', ctx);
  });

  subscription.on('publication', (ctx) => {
    console.log('📩 Message received:');
    console.log(JSON.stringify(ctx.data, null, 2));
    console.log('');
  });

  subscription.subscribe();
}

// Connect
console.log('🚀 Starting connection...');
centrifuge.connect();

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n👋 Disconnecting...');
  centrifuge.disconnect();
  process.exit(0);
});

// Keep the script running
setTimeout(() => {
  console.log('\n⏰ Test completed after 30 seconds');
  centrifuge.disconnect();
  process.exit(0);
}, 30000);