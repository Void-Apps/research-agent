// MongoDB initialization script
db = db.getSiblingDB('ai_research_agent');

// Create collections
db.createCollection('research_queries');
db.createCollection('research_results');
db.createCollection('cache_metadata');

// Create indexes for better performance
db.research_queries.createIndex({ "query_id": 1 }, { unique: true });
db.research_queries.createIndex({ "timestamp": 1 });
db.research_queries.createIndex({ "status": 1 });

db.research_results.createIndex({ "query_id": 1 }, { unique: true });
db.research_results.createIndex({ "created_at": 1 });
db.research_results.createIndex({ "expires_at": 1 });

db.cache_metadata.createIndex({ "query_hash": 1 }, { unique: true });
db.cache_metadata.createIndex({ "last_updated": 1 });

print('Database initialized successfully');