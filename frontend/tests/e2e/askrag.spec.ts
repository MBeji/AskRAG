import { test, expect, Page } from '@playwright/test';

// Configuration des tests
test.describe('AskRAG Authentication Flow', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await page.goto('http://localhost:5173');
  });

  test('should display login page for unauthenticated users', async () => {
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.locator('h2')).toContainText('Sign in to AskRAG');
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('should show validation errors for invalid login', async () => {
    await page.fill('input[name="email"]', 'invalid@test.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('.text-red-700')).toBeVisible();
  });

  test('should navigate to register page', async () => {
    await page.click('a[href="/register"]');
    await expect(page).toHaveURL(/.*\/register/);
    await expect(page.locator('h2')).toContainText('Register');
  });

  test('should show password visibility toggle', async () => {
    const passwordInput = page.locator('input[name="password"]');
    const toggleButton = page.locator('button[type="button"]').nth(0);

    // Password should be hidden initially
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Click toggle to show password
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');

    // Click toggle to hide password again
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should register new user and redirect to login', async () => {
    await page.click('a[href="/register"]');
    
    const timestamp = Date.now();
    await page.fill('input[name="username"]', `testuser${timestamp}`);
    await page.fill('input[name="email"]', `test${timestamp}@example.com`);
    await page.fill('input[name="password"]', 'TestPassword123!');
    
    await page.click('button[type="submit"]');
    
    // Should redirect to login page
    await expect(page).toHaveURL(/.*\/login/);
    
    // Should show success toast (if visible)
    const toast = page.locator('[aria-live="assertive"]');
    if (await toast.isVisible()) {
      await expect(toast).toContainText('Registration Successful');
    }
  });
});

test.describe('AskRAG Protected Routes', () => {
  test('should redirect to login for protected routes', async ({ page }) => {
    await page.goto('http://localhost:5173/chat');
    await expect(page).toHaveURL(/.*\/login/);

    await page.goto('http://localhost:5173/documents');
    await expect(page).toHaveURL(/.*\/login/);

    await page.goto('http://localhost:5173/settings');
    await expect(page).toHaveURL(/.*\/login/);
  });
});

test.describe('AskRAG Document Upload', () => {
  test.beforeEach(async ({ page }) => {
    // Mock successful login
    await page.goto('http://localhost:5173/login');
    
    // For testing purposes, we'll assume user can login
    // In real tests, you'd have test credentials
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    
    // Mock the login API response
    await page.route('**/api/v1/auth/login', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token',
          refresh_token: 'mock-refresh-token',
          user: {
            id: '1',
            email: 'test@example.com',
            firstName: 'Test',
            lastName: 'User',
            role: 'user',
            isActive: true,
            createdAt: new Date().toISOString()
          }
        })
      });
    });

    await page.click('button[type="submit"]');
  });

  test('should show document upload interface', async ({ page }) => {
    await page.goto('http://localhost:5173/documents');
    await expect(page.locator('h1')).toContainText('Documents');
    await expect(page.locator('input[type="file"]')).toBeVisible();
  });

  test('should validate file types', async ({ page }) => {
    await page.goto('http://localhost:5173/documents');
    
    // Mock file upload with invalid type
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.xyz',
      mimeType: 'application/unknown',
      buffer: Buffer.from('test content')
    });

    await page.click('button[type="submit"]');
    
    // Should show error message
    await expect(page.locator('.text-red-500')).toContainText('Format non supporté');
  });
});

test.describe('AskRAG Chat Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.addInitScript(() => {
      localStorage.setItem('auth-tokens', JSON.stringify({
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token'
      }));
    });
  });

  test('should display chat interface', async ({ page }) => {
    await page.goto('http://localhost:5173/chat');
    await expect(page.locator('h1')).toContainText('AI Chat Assistant');
    await expect(page.locator('input[placeholder*="Ask a question"]')).toBeVisible();
  });

  test('should send message and display response', async ({ page }) => {
    // Mock RAG API response
    await page.route('**/api/v1/rag/ask', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: 'This is a test response from the RAG system.',
          sources: ['document1.pdf', 'document2.txt']
        })
      });
    });

    await page.goto('http://localhost:5173/chat');
    
    const messageInput = page.locator('input[placeholder*="Ask a question"]');
    await messageInput.fill('What is machine learning?');
    await page.click('button[type="submit"]');

    // Should show user message
    await expect(page.locator('.bg-primary-600')).toContainText('What is machine learning?');
    
    // Should show AI response
    await expect(page.locator('.bg-gray-100')).toContainText('This is a test response from the RAG system.');
  });
});

test.describe('AskRAG Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.addInitScript(() => {
      localStorage.setItem('auth-tokens', JSON.stringify({
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token'
      }));
    });
  });

  test('should display settings tabs', async ({ page }) => {
    await page.goto('http://localhost:5173/settings');
    await expect(page.locator('h1')).toContainText('Settings');
    
    // Check tabs are present
    await expect(page.locator('button')).toContainText('API Configuration');
    await expect(page.locator('button')).toContainText('Model Settings');
    await expect(page.locator('button')).toContainText('RAG Parameters');
  });

  test('should save settings', async ({ page }) => {
    await page.goto('http://localhost:5173/settings');
    
    // Fill API key
    await page.fill('input[placeholder="sk-..."]', 'sk-test123456789');
    
    // Change model
    await page.selectOption('select', 'gpt-4');
    
    // Save settings
    await page.click('text=Save Settings');
    
    // Should show success alert
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('Settings saved successfully');
      dialog.accept();
    });
  });
});

test.describe('AskRAG Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.addInitScript(() => {
      localStorage.setItem('auth-tokens', JSON.stringify({
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token'
      }));
    });
  });

  test('should navigate between pages', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Test navigation links
    await page.click('a[href="/chat"]');
    await expect(page).toHaveURL(/.*\/chat/);
    
    await page.click('a[href="/documents"]');
    await expect(page).toHaveURL(/.*\/documents/);
    
    await page.click('a[href="/settings"]');
    await expect(page).toHaveURL(/.*\/settings/);
    
    await page.click('a[href="/"]');
    await expect(page).toHaveURL('http://localhost:5173/');
  });

  test('should show user dropdown menu', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Click user dropdown
    const userDropdown = page.locator('button').filter({ hasText: 'Test User' });
    await userDropdown.click();
    
    // Should show profile link
    await expect(page.locator('a[href="/profile"]')).toBeVisible();
    
    // Should show logout button
    await expect(page.locator('text=Sign out')).toBeVisible();
  });

  test('should logout user', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Click user dropdown
    const userDropdown = page.locator('button').filter({ hasText: 'Test User' });
    await userDropdown.click();
    
    // Click logout
    await page.click('text=Sign out');
    
    // Should redirect to login
    await expect(page).toHaveURL(/.*\/login/);
  });
});
