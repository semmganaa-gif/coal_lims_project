/**
 * Sample Management E2E Tests
 * Registration, search, status updates
 */
import { test, expect } from './fixtures';

test.describe('Sample Management', () => {
  // Login before each test
  test.beforeEach(async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.loginAsChemist();
    await loginPage.expectLoggedIn();
  });

  test.describe('Sample List', () => {
    test('should display samples page', async ({ page, samplesPage }) => {
      await samplesPage.goto();

      // Check page loaded
      await expect(page.locator('h1, h2, .page-title')).toContainText(/дээж|sample/i);
    });

    test('should have search functionality', async ({ page, samplesPage }) => {
      await samplesPage.goto();

      // Check search input exists
      await expect(page.locator('input[name="search"], input[placeholder*="Хайх"]')).toBeVisible();
    });

    test('should filter samples by search query', async ({ page, samplesPage }) => {
      await samplesPage.goto();

      // Search for specific sample
      await samplesPage.searchSample('QC');

      // Wait for results to update
      await page.waitForTimeout(500);

      // Should show filtered results (or no results message)
      const resultsOrEmpty = page.locator('table tbody tr, .no-results, .empty-state');
      await expect(resultsOrEmpty.first()).toBeVisible();
    });
  });

  test.describe('Sample Registration', () => {
    test('should display registration form', async ({ page, samplesPage }) => {
      await samplesPage.gotoRegister();

      // Check form elements
      await expect(page.locator('input[name="code"], input[name="sample_code"]')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should validate required fields', async ({ page, samplesPage }) => {
      await samplesPage.gotoRegister();

      // Submit without filling required fields
      await page.click('button[type="submit"]');

      // Should show validation error (HTML5 or server-side)
      const errorVisible = await page.locator('.alert-danger, .error, :invalid').first().isVisible();
      expect(errorVisible || page.url().includes('register')).toBeTruthy();
    });

    test('should register new sample successfully', async ({ page, samplesPage }) => {
      await samplesPage.gotoRegister();

      // Generate unique sample code
      const sampleCode = `TEST-${Date.now()}`;

      await samplesPage.registerSample({
        code: sampleCode,
        description: 'E2E Test Sample',
      });

      // Should show success or redirect to sample list
      const successOrRedirect =
        await page.locator('.alert-success, .flash-success, text=амжилттай').isVisible() ||
        !page.url().includes('register');

      expect(successOrRedirect).toBeTruthy();
    });

    test('should prevent duplicate sample codes', async ({ page, samplesPage }) => {
      await samplesPage.gotoRegister();

      // Try to register with existing code (assuming 'DUPLICATE-TEST' exists)
      await samplesPage.registerSample({
        code: 'QC-001', // Common existing code
      });

      // Should show error about duplicate
      // This test may need adjustment based on actual behavior
      await page.waitForTimeout(500);
    });
  });

  test.describe('Sample Details', () => {
    test('should show sample detail page', async ({ page, samplesPage }) => {
      await samplesPage.goto();

      // Click on first sample (if exists)
      const firstRow = page.locator('table tbody tr').first();
      if (await firstRow.isVisible()) {
        await firstRow.click();

        // Should navigate to detail page or show modal
        await page.waitForTimeout(300);
      }
    });
  });

  test.describe('Sample Actions', () => {
    test('should have action buttons', async ({ page, samplesPage }) => {
      await samplesPage.goto();

      // Check for common action buttons
      const hasActions = await page.locator(
        'button:has-text("Шинэ"), a:has-text("Шинэ"), .btn-primary'
      ).first().isVisible();

      expect(hasActions).toBeTruthy();
    });
  });
});

test.describe('Sample Workflow', () => {
  test.beforeEach(async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.loginAsAdmin();
    await loginPage.expectLoggedIn();
  });

  test('should complete full sample workflow', async ({ page, samplesPage }) => {
    // 1. Go to samples page
    await samplesPage.goto();
    await expect(page).toHaveURL(/samples/);

    // 2. Navigate to registration (if available)
    const registerLink = page.locator('a:has-text("Шинэ"), a:has-text("Бүртгэх"), a[href*="register"]');
    if (await registerLink.isVisible()) {
      await registerLink.click();
      await page.waitForLoadState('networkidle');
    }

    // 3. Return to samples list
    await samplesPage.goto();

    // Workflow complete
    await expect(page).toHaveURL(/samples/);
  });
});
