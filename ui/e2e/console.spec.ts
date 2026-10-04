import { expect, test } from "@playwright/test";

// Screens render, and the plan-approval workflow keeps its name end to end
// ("Approve plan" button -> "Plan approved" toast and log entry).

const SCREENS: [string, string][] = [
  ["#overview", "Single-line diagram"], ["#events", "Events"], ["#forecast", "Forecast"],
  ["#households", "Households"], ["#reports", "report"], ["#fleet", "Transformers"],
  ["#design", "Design system"], ["#blueprint", "Service blueprint"], ["#operator", "SAANJH"],
  ["#messages", "Household messages"], ["#status", "500 W"],
];

for (const [hash, text] of SCREENS) {
  test(`screen ${hash} renders`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(`/${hash}`);
    await expect(page.getByText(text, { exact: false }).first()).toBeVisible({ timeout: 20_000 });
    await page.screenshot({ path: `e2e/screenshots/${hash.slice(1)}.png`, fullPage: true });
    expect(errors).toEqual([]);
  });
}

test("approve a deficit plan", async ({ page }) => {
  await page.goto("/#overview");
  await page.evaluate(() => localStorage.removeItem("saanjh.actions.v1"));
  await page.reload();
  const approve = page.getByRole("button", { name: "Approve plan" });
  await expect(approve).toBeVisible({ timeout: 20_000 });
  await approve.click();
  await expect(page.getByText("Plan approved").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Plan approved" })).toBeDisabled();
});
