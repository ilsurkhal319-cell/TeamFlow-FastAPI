import { expect, test } from '@playwright/test';

test('публичный landing открывается без авторизации', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Управляй задачами команды/i })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Попробовать демо' })).toBeVisible();
});
