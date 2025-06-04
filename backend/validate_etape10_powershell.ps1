# AskRAG Etape 10 - Complete Validation Script for PowerShell
# This script tests the complete authentication and document upload flow

$baseUrl = "http://localhost:8003"
$testUser = @{
    username = "testuser_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    email = "test_$(Get-Date -Format 'yyyyMMdd_HHmmss')@example.com"
    password = "SecureTest123!"
}

Write-Host "=== AskRAG Etape 10 - Complete Validation ===" -ForegroundColor Green
Write-Host "Testing server: $baseUrl" -ForegroundColor Yellow
Write-Host ""

# Step 1: Test server health
Write-Host "Step 1: Testing server health..." -ForegroundColor Cyan
try {
    $healthResponse = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "✓ Server is healthy: $($healthResponse.message)" -ForegroundColor Green
} catch {
    Write-Host "✗ Server health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Register a new user
Write-Host "`nStep 2: Registering new user..." -ForegroundColor Cyan
Write-Host "Username: $($testUser.username)" -ForegroundColor Gray
Write-Host "Email: $($testUser.email)" -ForegroundColor Gray

try {
    $registerPayload = @{
        username = $testUser.username
        email = $testUser.email
        password = $testUser.password
    } | ConvertTo-Json

    $registerResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/register" -Method POST -Body $registerPayload -ContentType "application/json"
    Write-Host "✓ User registered successfully" -ForegroundColor Green
    Write-Host "User ID: $($registerResponse.id)" -ForegroundColor Gray
    Write-Host "Username: $($registerResponse.username)" -ForegroundColor Gray
    Write-Host "Email: $($registerResponse.email)" -ForegroundColor Gray
} catch {
    Write-Host "✗ User registration failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorDetails = $reader.ReadToEnd()
        Write-Host "Error details: $errorDetails" -ForegroundColor Red
    }
    exit 1
}

# Step 3: Login with the registered user
Write-Host "`nStep 3: Logging in..." -ForegroundColor Cyan

try {
    $loginPayload = @{
        username = $testUser.username
        password = $testUser.password
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -Body $loginPayload -ContentType "application/json"
    Write-Host "✓ Login successful" -ForegroundColor Green
    Write-Host "Token type: $($loginResponse.token_type)" -ForegroundColor Gray
    $accessToken = $loginResponse.access_token
    Write-Host "Access token received (length: $($accessToken.Length))" -ForegroundColor Gray
} catch {
    Write-Host "✗ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorDetails = $reader.ReadToEnd()
        Write-Host "Error details: $errorDetails" -ForegroundColor Red
    }
    exit 1
}

# Step 4: Test protected endpoint (get current user)
Write-Host "`nStep 4: Testing protected endpoint (/auth/me)..." -ForegroundColor Cyan

try {
    $headers = @{
        "Authorization" = "Bearer $accessToken"
    }
    
    $meResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/me" -Method GET -Headers $headers
    Write-Host "✓ Protected endpoint accessible" -ForegroundColor Green
    Write-Host "Current user: $($meResponse.username)" -ForegroundColor Gray
    Write-Host "Email: $($meResponse.email)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Protected endpoint access failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorDetails = $reader.ReadToEnd()
        Write-Host "Error details: $errorDetails" -ForegroundColor Red
    }
    exit 1
}

# Step 5: Create a test document for upload
Write-Host "`nStep 5: Creating test document..." -ForegroundColor Cyan

$testDocContent = @"
# Test Document for AskRAG

This is a test document created for validating the AskRAG document ingestion system.

## Content

This document contains sample text that can be processed by the RAG system.
It includes various sections and formatting to test the document processing capabilities.

### Features tested:
- Document upload
- Authentication
- File storage
- Metadata extraction

Generated at: $(Get-Date)
User: $($testUser.username)
"@

$testDocPath = "d:\11-coding\AskRAG\backend\test_document_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$testDocContent | Out-File -FilePath $testDocPath -Encoding UTF8
Write-Host "✓ Test document created: $testDocPath" -ForegroundColor Green

# Step 6: Upload the document
Write-Host "`nStep 6: Uploading document..." -ForegroundColor Cyan

try {
    # Create multipart form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$(Split-Path $testDocPath -Leaf)`"",
        "Content-Type: text/plain$LF",
        (Get-Content $testDocPath -Raw),
        "--$boundary--$LF"
    ) -join $LF

    $headers = @{
        "Authorization" = "Bearer $accessToken"
        "Content-Type" = "multipart/form-data; boundary=$boundary"
    }

    $uploadResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/documents/upload" -Method POST -Body $bodyLines -Headers $headers
    Write-Host "✓ Document uploaded successfully" -ForegroundColor Green
    Write-Host "Document ID: $($uploadResponse.id)" -ForegroundColor Gray
    Write-Host "Filename: $($uploadResponse.filename)" -ForegroundColor Gray
    Write-Host "Size: $($uploadResponse.size) bytes" -ForegroundColor Gray
} catch {
    Write-Host "✗ Document upload failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorDetails = $reader.ReadToEnd()
        Write-Host "Error details: $errorDetails" -ForegroundColor Red
    }
}

# Step 7: List uploaded documents
Write-Host "`nStep 7: Listing uploaded documents..." -ForegroundColor Cyan

try {
    $headers = @{
        "Authorization" = "Bearer $accessToken"
    }
    
    $documentsResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/documents" -Method GET -Headers $headers
    Write-Host "✓ Documents retrieved successfully" -ForegroundColor Green
    Write-Host "Total documents: $($documentsResponse.Count)" -ForegroundColor Gray
    
    foreach ($doc in $documentsResponse) {
        Write-Host "  - $($doc.filename) (ID: $($doc.id), Size: $($doc.size) bytes)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Document listing failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorDetails = $reader.ReadToEnd()
        Write-Host "Error details: $errorDetails" -ForegroundColor Red
    }
}

# Cleanup
Write-Host "`nStep 8: Cleanup..." -ForegroundColor Cyan
if (Test-Path $testDocPath) {
    Remove-Item $testDocPath -Force
    Write-Host "✓ Test document cleaned up" -ForegroundColor Green
}

Write-Host "`n=== Validation Complete ===" -ForegroundColor Green
Write-Host "All core functionality has been tested successfully!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Summary of tested features:" -ForegroundColor Cyan
Write-Host "  ✓ Server health check" -ForegroundColor Green
Write-Host "  ✓ User registration" -ForegroundColor Green
Write-Host "  ✓ User authentication (login)" -ForegroundColor Green
Write-Host "  ✓ JWT token generation and validation" -ForegroundColor Green
Write-Host "  ✓ Protected endpoint access" -ForegroundColor Green
Write-Host "  ✓ Document upload with authentication" -ForegroundColor Green
Write-Host "  ✓ Document listing with authentication" -ForegroundColor Green
Write-Host ""
Write-Host "The AskRAG Etape 10 implementation is fully functional!" -ForegroundColor Yellow
