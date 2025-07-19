import { test, expect } from '@playwright/test';

test.describe('Multi-Agent Development System - Hello World Project', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000');
    
    // Wait for the application to load
    await expect(page.locator('h1')).toContainText('Multi-Agent Development System');
  });

  test('should create a Hello World web page project', async ({ page }) => {
    // Step 1: Click the Start New Project button
    await page.getByRole('button', { name: 'Start New Project' }).click();
    
    // Step 2: Wait for the dialog to open
    await expect(page.getByText('Create New Project')).toBeVisible();
    
    // Step 3: Fill in project details
    const projectNameInput = page.locator('#name');
    const requirementsTextarea = page.locator('#requirements');
    
    await projectNameInput.fill('Hello World Web Page');
    await requirementsTextarea.fill(`Create a simple Hello World web page with the following requirements:
1. Display "Hello, World!" as the main heading
2. Include a welcome message paragraph
3. Add basic CSS styling with centered text and a nice color scheme
4. Make it responsive for mobile devices
5. Include a timestamp showing when the page was generated`);
    
    // Step 4: Submit the project
    await page.getByRole('button', { name: 'Create Project' }).click();
    
    // Step 5: Wait for the dialog to close and project to start
    await expect(page.getByText('Create New Project')).not.toBeVisible({ timeout: 10000 });
    
    // Step 6: Monitor the project progress
    // The actual UI shows project panels, not the data-testid elements
    // Wait for the project to appear in the projects panel
    await expect(page.getByText('Hello World Web Page')).toBeVisible({ timeout: 10000 });
    
    // Look for activity stream updates
    await expect(page.getByText(/Requirements Main Agent/i)).toBeVisible({ timeout: 30000 });
    
    // Wait for phase completion indicators
    // Since we don't have data-testid, we'll look for phase status text
    await expect(page.getByText(/Requirements.*completed/i)).toBeVisible({ timeout: 120000 });
    await expect(page.getByText(/Design.*completed/i)).toBeVisible({ timeout: 120000 });
    await expect(page.getByText(/Implementation.*completed/i)).toBeVisible({ timeout: 120000 });
    await expect(page.getByText(/Test.*completed/i)).toBeVisible({ timeout: 120000 });
    
    // Step 7: Verify project completion
    await expect(page.getByText(/Project completed/i)).toBeVisible({ timeout: 30000 });
  });

  test('should allow pausing and resuming the project', async ({ page }) => {
    // Start a new project
    await page.getByRole('button', { name: 'Start New Project' }).click();
    
    await page.locator('#name').fill('Pausable Hello World');
    await page.locator('#requirements').fill('Create a simple Hello World page');
    await page.getByRole('button', { name: 'Create Project' }).click();
    
    // Wait for the project to start
    await expect(page.getByText('Pausable Hello World')).toBeVisible({ timeout: 10000 });
    
    // Wait for activity to start
    await expect(page.getByText(/Requirements Main Agent/i)).toBeVisible({ timeout: 30000 });
    
    // Look for pause button in the project panel
    const projectPanel = page.locator(':has-text("Pausable Hello World")').locator('..');
    await projectPanel.getByRole('button', { name: /pause/i }).click();
    
    // Verify the project is paused
    await expect(projectPanel).toContainText(/paused/i);
    
    // Wait a moment
    await page.waitForTimeout(2000);
    
    // Resume the project
    await projectPanel.getByRole('button', { name: /resume/i }).click();
    
    // Verify the project is no longer paused
    await expect(projectPanel).not.toContainText(/paused/i);
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Start a project with invalid requirements
    await page.getByRole('button', { name: 'Start New Project' }).click();
    
    // Try to create project with empty fields
    await page.getByRole('button', { name: 'Create Project' }).click();
    
    // Should show validation error - the error appears as plain text
    await expect(page.getByText('Project name is required')).toBeVisible();
    
    // Fill in name but leave requirements empty
    await page.locator('#name').fill('Test Project');
    await page.getByRole('button', { name: 'Create Project' }).click();
    
    // Should show requirements error
    await expect(page.getByText('Requirements are required')).toBeVisible();
    
    // Cancel the dialog
    await page.getByRole('button', { name: 'Cancel' }).click();
    
    // Dialog should close
    await expect(page.getByText('Create New Project')).not.toBeVisible();
  });
});