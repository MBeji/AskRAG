// Test script to verify frontend-backend integration
const axios = require('axios');

const FRONTEND_URL = 'http://localhost:5173';
const BACKEND_URL = 'http://localhost:8003';

async function testBackendConnection() {
    console.log('🧪 Testing Backend Connection...');
    try {
        const response = await axios.get(`${BACKEND_URL}/api/v1/health`);
        console.log('✅ Backend health check:', response.status);
        return true;
    } catch (error) {
        console.log('❌ Backend connection failed:', error.message);
        return false;
    }
}

async function testBackendAuth() {
    console.log('🧪 Testing Backend Authentication...');
    try {
        // Test with our known working credentials
        const loginData = {
            email: 'integration@test.com',
            password: 'TestPassword123!'
        };
        
        const response = await axios.post(`${BACKEND_URL}/api/v1/auth/login`, loginData);
        console.log('✅ Backend login successful:', response.status);
        console.log('🔑 Access token received:', !!response.data.access_token);
        return response.data.access_token;
    } catch (error) {
        console.log('❌ Backend authentication failed:', error.message);
        return null;
    }
}

async function testProtectedEndpoint(token) {
    console.log('🧪 Testing Protected Endpoint...');
    try {
        const response = await axios.get(`${BACKEND_URL}/api/v1/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        console.log('✅ Protected endpoint accessible:', response.status);
        console.log('👤 User data:', response.data);
        return true;
    } catch (error) {
        console.log('❌ Protected endpoint failed:', error.message);
        return false;
    }
}

async function testFrontendAccess() {
    console.log('🧪 Testing Frontend Access...');
    try {
        const response = await axios.get(FRONTEND_URL);
        console.log('✅ Frontend accessible:', response.status);
        return true;
    } catch (error) {
        console.log('❌ Frontend access failed:', error.message);
        return false;
    }
}

async function runIntegrationTests() {
    console.log('🚀 Starting Frontend-Backend Integration Tests\n');
    
    const frontendOk = await testFrontendAccess();
    const backendOk = await testBackendConnection();
    
    if (!frontendOk || !backendOk) {
        console.log('\n❌ Basic connectivity failed. Check if servers are running.');
        return;
    }
    
    const token = await testBackendAuth();
    if (token) {
        await testProtectedEndpoint(token);
    }
    
    console.log('\n✅ Integration tests completed!');
    console.log('📝 Next steps:');
    console.log('   1. Open http://localhost:5173 in browser');
    console.log('   2. Test user registration/login in UI');
    console.log('   3. Test protected features');
}

// Run the tests
runIntegrationTests().catch(console.error);
