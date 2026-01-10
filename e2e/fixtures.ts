/**
 * E2E Test Fixtures
 * Reusable test utilities and page objects
 */
import { test as base, expect, Page } from '@playwright/test';

// Test user credentials (test environment only)
export const TEST_USERS = {
  admin: {
    username: 'admin',
    password: 'admin123',
  },
  chemist: {
    username: 'chemist1',
    password: 'chemist123',
  },
};

// Page Object for Login
export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async login(username: string, password: string) {
    await this.page.fill('input[name="username"]', username);
    await this.page.fill('input[name="password"]', password);
    await this.page.click('button[type="submit"]');
  }

  async loginAsAdmin() {
    await this.login(TEST_USERS.admin.username, TEST_USERS.admin.password);
  }

  async loginAsChemist() {
    await this.login(TEST_USERS.chemist.username, TEST_USERS.chemist.password);
  }

  async expectLoggedIn() {
    // Wait for redirect to dashboard or index
    await expect(this.page).toHaveURL(/\/(index|dashboard)?$/);
  }

  async expectLoginError() {
    await expect(this.page.locator('.alert-danger, .flash-error')).toBeVisible();
  }
}

// Page Object for Samples
export class SamplesPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/samples');
  }

  async gotoRegister() {
    await this.page.goto('/samples/register');
  }

  async registerSample(data: {
    code: string;
    client?: string;
    sampleType?: string;
    description?: string;
  }) {
    await this.page.fill('input[name="code"], input[name="sample_code"]', data.code);

    if (data.client) {
      await this.page.selectOption('select[name="client"]', data.client);
    }

    if (data.sampleType) {
      await this.page.selectOption('select[name="sample_type"]', data.sampleType);
    }

    if (data.description) {
      await this.page.fill('textarea[name="description"]', data.description);
    }

    await this.page.click('button[type="submit"]');
  }

  async searchSample(query: string) {
    await this.page.fill('input[name="search"], input[placeholder*="Хайх"]', query);
    await this.page.keyboard.press('Enter');
  }

  async expectSampleVisible(code: string) {
    await expect(this.page.locator(`text=${code}`)).toBeVisible();
  }
}

// Page Object for Analysis
export class AnalysisPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/analysis');
  }

  async gotoWorkspace() {
    await this.page.goto('/analysis/workspace');
  }

  async selectAnalysisType(type: string) {
    await this.page.click(`text=${type}`);
  }

  async enterResult(sampleCode: string, value: string) {
    const row = this.page.locator(`tr:has-text("${sampleCode}")`);
    await row.locator('input[type="number"], input[name*="result"]').fill(value);
  }

  async saveResults() {
    await this.page.click('button:has-text("Хадгалах"), button[type="submit"]');
  }

  async expectResultSaved() {
    await expect(this.page.locator('.alert-success, .flash-success, text=амжилттай')).toBeVisible();
  }
}

// Custom test fixture with page objects
type Fixtures = {
  loginPage: LoginPage;
  samplesPage: SamplesPage;
  analysisPage: AnalysisPage;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  samplesPage: async ({ page }, use) => {
    await use(new SamplesPage(page));
  },
  analysisPage: async ({ page }, use) => {
    await use(new AnalysisPage(page));
  },
});

export { expect };
