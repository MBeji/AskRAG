// Test d'intégration Frontend-Backend pour AskRAG
// Teste la communication entre React frontend et Flask backend

console.log('🚀 Test d\'intégration Frontend-Backend AskRAG');

// Test 1: Health check du backend
async function testBackendHealth() {
    try {
        console.log('📡 Test 1: Health check backend...');
        const response = await fetch('http://localhost:8000/health');
        const data = await response.json();
        console.log('✅ Backend health:', data);
        return true;
    } catch (error) {
        console.error('❌ Backend health failed:', error.message);
        return false;
    }
}

// Test 2: Login avec credentials de test
async function testLogin() {
    try {
        console.log('🔐 Test 2: Login authentication...');
        const response = await fetch('http://localhost:8000/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: 'test@example.com',
                password: 'test123'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Login successful:', {
                user: data.user.email,
                hasToken: !!data.tokens.accessToken
            });
            return data.tokens.accessToken;
        } else {
            console.error('❌ Login failed:', response.status);
            return null;
        }
    } catch (error) {
        console.error('❌ Login error:', error.message);
        return null;
    }
}

// Test 3: Test d'un endpoint protégé (si disponible)
async function testProtectedEndpoint(token) {
    try {
        console.log('🔒 Test 3: Protected endpoint...');
        const response = await fetch('http://localhost:8000/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Protected endpoint accessible:', data);
            return true;
        } else {
            console.log('ℹ️ Protected endpoint not available (expected)');
            return false;
        }
    } catch (error) {
        console.log('ℹ️ Protected endpoint test:', error.message);
        return false;
    }
}

// Exécution des tests
async function runIntegrationTests() {
    console.log('\n' + '='.repeat(50));
    console.log('🧪 TESTS D\'INTÉGRATION ASKRAG');
    console.log('='.repeat(50));
    
    const healthOk = await testBackendHealth();
    if (!healthOk) {
        console.log('❌ Backend non disponible - arrêt des tests');
        return;
    }
    
    console.log('\n' + '-'.repeat(30));
    const token = await testLogin();
    
    if (token) {
        console.log('\n' + '-'.repeat(30));
        await testProtectedEndpoint(token);
    }
    
    console.log('\n' + '='.repeat(50));
    console.log('✅ Tests d\'intégration terminés');
    console.log('🌐 Frontend: http://localhost:5173');
    console.log('🔧 Backend: http://localhost:8000');
    console.log('='.repeat(50));
}

// Exécuter les tests
runIntegrationTests();
