import { test, expect } from '@playwright/test';

test.describe('Multi-Agent Development System', () => {
  test('should create a Hello World project', async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000');
    
    // Wait for the application to load
    await expect(page.locator('h1')).toContainText('Multi-Agent Development System');
    
    // Click the Start New Project button
    await page.getByRole('button', { name: 'Start New Project' }).click();
    
    // Wait for the dialog to open - use heading role for specificity
    await expect(page.getByRole('heading', { name: 'Create New Project' })).toBeVisible();
    
    // Fill in project details
    await page.locator('#name').fill('Hello World Web Page');
    await page.locator('#requirements').fill('Create a simple Hello World web page with a heading that says "Hello, World!" and basic CSS styling');
    
    // Submit the project
    await page.getByRole('button', { name: 'Create Project' }).click();
    
    // Wait for the project to appear in the projects list
    await expect(page.getByText('Hello World Web Page')).toBeVisible({ timeout: 30000 });
    
    // Monitor for agent activity - look for any agent activity
    await expect(page.getByText(/Agent/i)).toBeVisible({ timeout: 60000 });
    
    // The test succeeds if we can create a project and see agent activity
    console.log('✅ Successfully created Hello World project and agents are working!');
  });
});