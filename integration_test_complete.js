#!/usr/bin/env node
/**
 * Complete Frontend-Backend Integration Test
 * Tests the authentication flow between React frontend and FastAPI backend
 */

import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';

const FRONTEND_URL = 'http://localhost:5173';
const BACKEND_URL = 'http://localhost:8003';
const TEST_USER = {
    email: 'integration@test.com',
    password: 'TestPassword123!'
};

class IntegrationTester {
    constructor() {
        this.results = [];
        this.authToken = null;
    }

    log(message, status = 'INFO') {
        const timestamp = new Date().toISOString();
        const logEntry = `[${timestamp}] [${status}] ${message}`;
        console.log(logEntry);
        this.results.push({ timestamp, status, message });
    }

    async testEndpoint(name, url, options = {}) {
        try {
            this.log(`Testing ${name}: ${url}`, 'TEST');
            const response = await fetch(url, options);
            const statusText = response.ok ? 'SUCCESS' : 'FAILED';
            this.log(`${name} - Status: ${response.status} ${response.statusText}`, statusText);
            
            if (response.ok) {
                try {
                    const data = await response.json();
                    return { success: true, data, status: response.status };
                } catch (e) {
                    const text = await response.text();
                    return { success: true, data: text, status: response.status };
                }
            } else {
                const errorText = await response.text();
                return { success: false, error: errorText, status: response.status };
            }
        } catch (error) {
            this.log(`${name} - Network Error: ${error.message}`, 'ERROR');
            return { success: false, error: error.message };
        }
    }

    async testBackendConnectivity() {
        this.log('=== BACKEND CONNECTIVITY TESTS ===', 'SECTION');
        
        // Test root endpoint
        const rootTest = await this.testEndpoint('Backend Root', `${BACKEND_URL}/`);
        if (!rootTest.success) {
            this.log('Backend is not accessible! Check if working_auth_server.py is running on port 8003', 'ERROR');
            return false;
        }
        
        this.log(`Backend Message: ${rootTest.data.message}`, 'INFO');
        return true;
    }

    async testBackendAuth() {
        this.log('=== BACKEND AUTHENTICATION TESTS ===', 'SECTION');
        
        // Test login endpoint
        const loginTest = await this.testEndpoint('Backend Login', `${BACKEND_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(TEST_USER)
        });

        if (!loginTest.success) {
            this.log(`Login failed: ${loginTest.error}`, 'ERROR');
            return false;
        }

        this.authToken = loginTest.data.access_token;
        this.log('Login successful! Token received.', 'SUCCESS');
        this.log(`User: ${loginTest.data.user.email} (ID: ${loginTest.data.user.id})`, 'INFO');

        // Test protected endpoint
        const meTest = await this.testEndpoint('Protected Endpoint', `${BACKEND_URL}/api/v1/auth/me`, {
            headers: { 'Authorization': `Bearer ${this.authToken}` }
        });

        if (!meTest.success) {
            this.log(`Protected endpoint failed: ${meTest.error}`, 'ERROR');
            return false;
        }

        this.log('Protected endpoint accessible!', 'SUCCESS');
        return true;
    }

    async testFrontendConnectivity() {
        this.log('=== FRONTEND CONNECTIVITY TESTS ===', 'SECTION');
        
        const frontendTest = await this.testEndpoint('Frontend Root', FRONTEND_URL);
        if (!frontendTest.success) {
            this.log('Frontend is not accessible! Check if npm run dev is running on port 5173', 'ERROR');
            return false;
        }

        this.log('Frontend is accessible!', 'SUCCESS');
        return true;
    }

    async testFrontendConfiguration() {
        this.log('=== FRONTEND CONFIGURATION TESTS ===', 'SECTION');
        
        // Check environment file
        const envPath = path.join(process.cwd(), 'frontend', '.env.development');
        try {
            const envContent = fs.readFileSync(envPath, 'utf8');
            const apiUrlMatch = envContent.match(/VITE_API_URL=(.+)/);
            if (apiUrlMatch) {
                const apiUrl = apiUrlMatch[1];
                this.log(`Frontend API URL configured: ${apiUrl}`, 'INFO');
                if (apiUrl === BACKEND_URL) {
                    this.log('Frontend API URL correctly points to backend!', 'SUCCESS');
                    return true;
                } else {
                    this.log(`Frontend API URL mismatch! Expected: ${BACKEND_URL}, Found: ${apiUrl}`, 'ERROR');
                    return false;
                }
            } else {
                this.log('VITE_API_URL not found in environment file', 'ERROR');
                return false;
            }
        } catch (error) {
            this.log(`Could not read environment file: ${error.message}`, 'ERROR');
            return false;
        }
    }

    async testCORSConfiguration() {
        this.log('=== CORS CONFIGURATION TESTS ===', 'SECTION');
        
        // Test preflight request
        const corsTest = await this.testEndpoint('CORS Preflight', `${BACKEND_URL}/api/v1/auth/login`, {
            method: 'OPTIONS',
            headers: {
                'Origin': FRONTEND_URL,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        });

        if (corsTest.success) {
            this.log('CORS preflight successful!', 'SUCCESS');
            return true;
        } else {
            this.log('CORS preflight failed - this may cause frontend issues', 'WARNING');
            return false;
        }
    }

    async generateReport() {
        this.log('=== INTEGRATION TEST REPORT ===', 'SECTION');
        
        const summary = {
            total: this.results.length,
            success: this.results.filter(r => r.status === 'SUCCESS').length,
            errors: this.results.filter(r => r.status === 'ERROR').length,
            warnings: this.results.filter(r => r.status === 'WARNING').length
        };

        this.log(`Total Tests: ${summary.total}`, 'INFO');
        this.log(`Successful: ${summary.success}`, 'SUCCESS');
        this.log(`Errors: ${summary.errors}`, summary.errors > 0 ? 'ERROR' : 'INFO');
        this.log(`Warnings: ${summary.warnings}`, summary.warnings > 0 ? 'WARNING' : 'INFO');

        // Save detailed report
        const reportPath = path.join(process.cwd(), 'integration_test_report.json');
        const report = {
            timestamp: new Date().toISOString(),
            summary,
            results: this.results,
            recommendations: this.generateRecommendations(summary)
        };

        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        this.log(`Detailed report saved to: ${reportPath}`, 'INFO');

        return summary;
    }

    generateRecommendations(summary) {
        const recommendations = [];
        
        if (summary.errors > 0) {
            recommendations.push('Fix critical errors before proceeding with frontend testing');
        }
        
        if (this.authToken) {
            recommendations.push('Backend authentication is working - proceed with frontend UI testing');
            recommendations.push('Test login/logout flow in the React application');
            recommendations.push('Test protected routes and token refresh');
        } else {
            recommendations.push('Backend authentication failed - check server logs');
        }

        recommendations.push('Open http://localhost:5173/login and test manual login');
        recommendations.push('Check browser console for any JavaScript errors');
        recommendations.push('Verify React AuthContext is properly managing authentication state');

        return recommendations;
    }

    async runAllTests() {
        this.log('🚀 Starting Complete Frontend-Backend Integration Tests', 'SECTION');
        
        const backendConnectivity = await this.testBackendConnectivity();
        const frontendConnectivity = await this.testFrontendConnectivity();
        const frontendConfig = await this.testFrontendConfiguration();
        const corsConfig = await this.testCORSConfiguration();
        
        let backendAuth = false;
        if (backendConnectivity) {
            backendAuth = await this.testBackendAuth();
        }

        const summary = await this.generateReport();
        
        this.log('🎯 INTEGRATION TEST RESULTS:', 'SECTION');
        this.log(`✅ Backend Connectivity: ${backendConnectivity ? 'PASS' : 'FAIL'}`, backendConnectivity ? 'SUCCESS' : 'ERROR');
        this.log(`✅ Frontend Connectivity: ${frontendConnectivity ? 'PASS' : 'FAIL'}`, frontendConnectivity ? 'SUCCESS' : 'ERROR');
        this.log(`✅ Frontend Configuration: ${frontendConfig ? 'PASS' : 'FAIL'}`, frontendConfig ? 'SUCCESS' : 'ERROR');
        this.log(`✅ CORS Configuration: ${corsConfig ? 'PASS' : 'FAIL'}`, corsConfig ? 'SUCCESS' : 'WARNING');
        this.log(`✅ Backend Authentication: ${backendAuth ? 'PASS' : 'FAIL'}`, backendAuth ? 'SUCCESS' : 'ERROR');

        if (backendConnectivity && frontendConnectivity && frontendConfig && backendAuth) {
            this.log('🎉 READY FOR FRONTEND UI TESTING!', 'SUCCESS');
            this.log('Next steps:', 'INFO');
            this.log('1. Open http://localhost:5173/login', 'INFO');
            this.log('2. Test login with: integration@test.com / TestPassword123!', 'INFO');
            this.log('3. Verify authentication state in React app', 'INFO');
        } else {
            this.log('❌ Fix the above issues before proceeding', 'ERROR');
        }

        return summary;
    }
}

// Run the tests
const tester = new IntegrationTester();
tester.runAllTests()
    .then(summary => {
        process.exit(summary.errors > 0 ? 1 : 0);
    })
    .catch(error => {
        console.error('Test runner failed:', error);
        process.exit(1);
    });
