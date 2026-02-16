// MongoDB initialization script

// Create databases and collections for each service
const databases = ['orders_mongo', 'analytics_mongo', 'store_mongo'];

databases.forEach(dbName => {
    db = db.getSiblingDB(dbName);

    // Create common collections
    db.createCollection('events');
    db.events.createIndex({ 'timestamp': -1 });
    db.events.createIndex({ 'event_type': 1 });

    print(`Database ${dbName} initialized`);
});

// Orders database specific setup
db = db.getSiblingDB('orders_mongo');
db.createCollection('order_events');
db.order_events.createIndex({ 'order_id': 1, 'timestamp': -1 });
db.order_events.createIndex({ 'user_id': 1 });

// Analytics database specific setup
db = db.getSiblingDB('analytics_mongo');
db.createCollection('page_views');
db.page_views.createIndex({ 'timestamp': -1 });
db.page_views.createIndex({ 'user_id': 1 });
db.page_views.createIndex({ 'session_id': 1 });

db.createCollection('user_events');
db.user_events.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.user_events.createIndex({ 'event_type': 1 });

// Store database specific setup
db = db.getSiblingDB('store_mongo');
db.createCollection('product_reviews');
db.product_reviews.createIndex({ 'product_id': 1, 'created_at': -1 });
db.product_reviews.createIndex({ 'user_id': 1 });

db.createCollection('product_analytics');
db.product_analytics.createIndex({ 'product_id': 1, 'date': -1 });

print('MongoDB initialization completed');
