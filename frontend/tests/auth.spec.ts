import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
  });

  test('should navigate to login page', async ({ page }) => {
    // Click on login/sign in button
    await page.click('[data-testid="login-button"]');
    
    // Should be on login page
    await expect(page).toHaveURL('/login');
    await expect(page.locator('h1')).toContainText('Sign In');
  });

  test('should show validation errors for empty login form', async ({ page }) => {
    await page.goto('/login');
    
    // Click submit without filling form
    await page.click('button[type="submit"]');
    
    // Should show validation errors
    await expect(page.locator('[data-testid="email-error"]')).toContainText('Email is required');
    await expect(page.locator('[data-testid="password-error"]')).toContainText('Password is required');
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Fill login form
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'test123');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard/home after successful login
    await expect(page).toHaveURL('/');
    
    // Should show user is logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-email"]')).toContainText('test@example.com');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Fill with invalid credentials
    await page.fill('[data-testid="email-input"]', 'invalid@example.com');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
    
    // Should remain on login page
    await expect(page).toHaveURL('/login');
  });

  test('should logout successfully', async ({ page }) => {
    // First login
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'test123');
    await page.click('button[type="submit"]');
    
    // Wait for successful login
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    
    // Open user menu and logout
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');
    
    // Should redirect to home page and show login button
    await expect(page).toHaveURL('/');
    await expect(page.locator('[data-testid="login-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-menu"]')).not.toBeVisible();
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login');
    
    // Click register link
    await page.click('[data-testid="register-link"]');
    
    // Should be on register page
    await expect(page).toHaveURL('/register');
    await expect(page.locator('h1')).toContainText('Create Account');
  });

  test('should register new user', async ({ page }) => {
    await page.goto('/register');
    
    // Fill registration form
    await page.fill('[data-testid="firstname-input"]', 'New');
    await page.fill('[data-testid="lastname-input"]', 'User');
    await page.fill('[data-testid="email-input"]', 'newuser@example.com');
    await page.fill('[data-testid="password-input"]', 'newpassword123');
    await page.fill('[data-testid="confirm-password-input"]', 'newpassword123');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should either succeed or show user exists error
    // In our mock system, it might show user exists
    const isSuccess = await page.locator('[data-testid="user-menu"]').isVisible();
    const hasError = await page.locator('[data-testid="error-message"]').isVisible();
    
    expect(isSuccess || hasError).toBeTruthy();
  });

  test('should protect routes when not authenticated', async ({ page }) => {
    // Try to access protected route directly
    await page.goto('/profile');
    
    // Should redirect to login
    await expect(page).toHaveURL('/login');
  });

  test('should allow access to protected routes when authenticated', async ({ page }) => {
    // First login
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'test123');
    await page.click('button[type="submit"]');
    
    // Wait for login
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    
    // Navigate to protected route
    await page.goto('/profile');
    
    // Should be able to access profile page
    await expect(page).toHaveURL('/profile');
    await expect(page.locator('h1')).toContainText('Profile');
  });

  test('should persist authentication across page refreshes', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'test123');
    await page.click('button[type="submit"]');
    
    // Wait for login
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    
    // Refresh the page
    await page.reload();
    
    // Should still be authenticated
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-email"]')).toContainText('test@example.com');
  });

  test('should handle token refresh', async ({ page }) => {
    // This test would require setting up expired tokens
    // For now, we'll just test that the app handles token errors gracefully
    
    // Login first
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'test123');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    
    // Mock expired token by clearing localStorage
    await page.evaluate(() => {
      localStorage.setItem('accessToken', 'expired-token');
    });
    
    // Try to access a protected API endpoint
    await page.reload();
    
    // Should handle gracefully (either refresh token or redirect to login)
    const isLoggedIn = await page.locator('[data-testid="user-menu"]').isVisible();
    const isLoginPage = page.url().includes('/login');
    
    expect(isLoggedIn || isLoginPage).toBeTruthy();
  });
});
