// Initialize MongoDB for Unpod services

// Switch to unpod database
db = db.getSiblingDB('unpod_mongo');

// Create collections with indexes
db.createCollection('messages');
db.messages.createIndex({ "thread_id": 1, "created_at": -1 });
db.messages.createIndex({ "user_id": 1 });
db.messages.createIndex({ "organization_id": 1 });

db.createCollection('call_logs');
db.call_logs.createIndex({ "call_id": 1 }, { unique: true });
db.call_logs.createIndex({ "organization_id": 1, "created_at": -1 });
db.call_logs.createIndex({ "agent_id": 1 });

db.createCollection('analytics_events');
db.analytics_events.createIndex({ "event_type": 1, "timestamp": -1 });
db.analytics_events.createIndex({ "user_id": 1 });
db.analytics_events.createIndex({ "organization_id": 1 });

// Create application user
db.createUser({
    user: "unpod_app",
    pwd: process.env.MONGO_APP_PASSWORD || "changeme",
    roles: [
        { role: "readWrite", db: "unpod_mongo" }
    ]
});

print("MongoDB initialization complete for Unpod");
