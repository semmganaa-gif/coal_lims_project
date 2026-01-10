/**
 * Authentication E2E Tests
 * Login, logout, session management
 */
import { test, expect, TEST_USERS } from './fixtures';

test.describe('Authentication', () => {
  test.describe('Login', () => {
    test('should display login page', async ({ page, loginPage }) => {
      await loginPage.goto();

      // Check login form elements
      await expect(page.locator('input[name="username"]')).toBeVisible();
      await expect(page.locator('input[name="password"]')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should login with valid admin credentials', async ({ loginPage }) => {
      await loginPage.goto();
      await loginPage.loginAsAdmin();
      await loginPage.expectLoggedIn();
    });

    test('should login with valid chemist credentials', async ({ loginPage }) => {
      await loginPage.goto();
      await loginPage.loginAsChemist();
      await loginPage.expectLoggedIn();
    });

    test('should show error with invalid credentials', async ({ page, loginPage }) => {
      await loginPage.goto();
      await loginPage.login('invalid_user', 'wrong_password');

      // Should stay on login page with error
      await expect(page).toHaveURL(/login/);
      await loginPage.expectLoginError();
    });

    test('should show error with empty credentials', async ({ page, loginPage }) => {
      await loginPage.goto();
      await page.click('button[type="submit"]');

      // HTML5 validation or server-side error
      await expect(page).toHaveURL(/login/);
    });
  });

  test.describe('Logout', () => {
    test('should logout successfully', async ({ page, loginPage }) => {
      // Login first
      await loginPage.goto();
      await loginPage.loginAsAdmin();
      await loginPage.expectLoggedIn();

      // Click logout
      await page.click('a:has-text("Гарах"), a[href*="logout"]');

      // Should redirect to login
      await expect(page).toHaveURL(/login/);
    });
  });

  test.describe('Protected Routes', () => {
    test('should redirect to login when accessing protected page', async ({ page }) => {
      // Try to access samples without login
      await page.goto('/samples');

      // Should redirect to login
      await expect(page).toHaveURL(/login/);
    });

    test('should redirect to login when accessing analysis', async ({ page }) => {
      await page.goto('/analysis');
      await expect(page).toHaveURL(/login/);
    });

    test('should redirect to login when accessing admin', async ({ page }) => {
      await page.goto('/admin');
      await expect(page).toHaveURL(/login/);
    });
  });

  test.describe('Session', () => {
    test('should maintain session across page navigation', async ({ page, loginPage }) => {
      await loginPage.goto();
      await loginPage.loginAsAdmin();
      await loginPage.expectLoggedIn();

      // Navigate to different pages
      await page.goto('/samples');
      await expect(page).not.toHaveURL(/login/);

      await page.goto('/analysis');
      await expect(page).not.toHaveURL(/login/);
    });
  });
});
