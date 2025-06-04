// MongoDB initialization script for AskRAG
// This script will be executed when MongoDB container starts for the first time

print('Starting AskRAG database initialization...');

// Switch to the AskRAG database
db = db.getSiblingDB('askrag_db');

// Create a non-admin user for the application
db.createUser({
  user: 'askrag_user',
  pwd: 'askrag_password_2024',
  roles: [
    {
      role: 'readWrite',
      db: 'askrag_db'
    }
  ]
});

// Create collections with validation
print('Creating collections...');

// Users collection
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['email', 'hashed_password', 'created_at'],
      properties: {
        email: {
          bsonType: 'string',
          pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        },
        hashed_password: {
          bsonType: 'string'
        },
        full_name: {
          bsonType: 'string'
        },
        is_active: {
          bsonType: 'bool'
        },
        created_at: {
          bsonType: 'date'
        },
        updated_at: {
          bsonType: 'date'
        }
      }
    }
  }
});

// Documents collection
db.createCollection('documents', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['filename', 'content_type', 'user_id', 'created_at'],
      properties: {
        filename: {
          bsonType: 'string'
        },
        content_type: {
          bsonType: 'string'
        },
        file_size: {
          bsonType: 'long'
        },
        content: {
          bsonType: 'string'
        },
        user_id: {
          bsonType: 'objectId'
        },
        created_at: {
          bsonType: 'date'
        },
        updated_at: {
          bsonType: 'date'
        }
      }
    }
  }
});

// Chats collection
db.createCollection('chats', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['title', 'user_id', 'created_at'],
      properties: {
        title: {
          bsonType: 'string'
        },
        user_id: {
          bsonType: 'objectId'
        },
        messages: {
          bsonType: 'array',
          items: {
            bsonType: 'object',
            required: ['content', 'role', 'timestamp'],
            properties: {
              content: {
                bsonType: 'string'
              },
              role: {
                bsonType: 'string',
                enum: ['user', 'assistant']
              },
              timestamp: {
                bsonType: 'date'
              }
            }
          }
        },
        created_at: {
          bsonType: 'date'
        },
        updated_at: {
          bsonType: 'date'
        }
      }
    }
  }
});

// Create indexes for better performance
print('Creating indexes...');

// Users indexes
db.users.createIndex({ 'email': 1 }, { unique: true });
db.users.createIndex({ 'created_at': -1 });

// Documents indexes
db.documents.createIndex({ 'user_id': 1 });
db.documents.createIndex({ 'filename': 1 });
db.documents.createIndex({ 'created_at': -1 });
db.documents.createIndex({ 'content': 'text' });

// Chats indexes
db.chats.createIndex({ 'user_id': 1 });
db.chats.createIndex({ 'created_at': -1 });
db.chats.createIndex({ 'title': 1 });

// Insert sample data
print('Inserting sample data...');

// Sample user
const sampleUserId = new ObjectId();
db.users.insertOne({
  _id: sampleUserId,
  email: 'demo@askrag.com',
  hashed_password: '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj67HS8O8Gfq', // 'demo123'
  full_name: 'Demo User',
  is_active: true,
  created_at: new Date(),
  updated_at: new Date()
});

// Sample document
const sampleDocId = new ObjectId();
db.documents.insertOne({
  _id: sampleDocId,
  filename: 'welcome.txt',
  content_type: 'text/plain',
  file_size: 156,
  content: 'Welcome to AskRAG! This is a sample document that demonstrates the RAG (Retrieval-Augmented Generation) capabilities of our application.',
  user_id: sampleUserId,
  created_at: new Date(),
  updated_at: new Date()
});

// Sample chat
db.chats.insertOne({
  title: 'Welcome Chat',
  user_id: sampleUserId,
  messages: [
    {
      content: 'Hello! How can I help you with your documents today?',
      role: 'assistant',
      timestamp: new Date()
    }
  ],
  created_at: new Date(),
  updated_at: new Date()
});

print('AskRAG database initialization completed successfully!');
print('Created collections: users, documents, chats');
print('Created user: demo@askrag.com (password: demo123)');
print('Sample data inserted successfully.');
