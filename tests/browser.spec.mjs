import { test, expect } from "@playwright/test";
test("review queue, keyboard judgment, reload and exported history", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.clock.install({ time: new Date("2026-09-18T12:00:00Z") });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Reference business bundle" }),
  ).toBeVisible();
  await page.getByLabel("Find a case").fill("candidate a");
  await page
    .getByRole("button", { name: "Candidate A business bundle" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Candidate A business bundle" }),
  ).toBeFocused();
  await page.getByLabel("Decision", { exact: true }).selectOption("revise");
  await page
    .getByLabel("Evidence and rationale")
    .fill("The revenue formula adds units and price; inspect B8.");
  await page.getByRole("button", { name: "Save review revision" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toHaveText(
    "Review revision saved locally.",
  );
  await expect(page.getByLabel("Evidence and rationale")).toBeFocused();
  await page.screenshot({path:"test-results/reviewer-desktop.png",fullPage:true});
  await page.reload();
  await expect(page.locator("#history")).toContainText("candidate-a: revise");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export review history" }).click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  let body = "";
  for await (const chunk of stream) body += chunk;
  const data = JSON.parse(body);
  expect(data.history).toHaveLength(1);
  expect(data.certification).toBe(false);
  await page.getByLabel("Find a case").fill("not a case");
  await expect(page.getByText("No matching cases.")).toBeVisible();
  expect(errors).toEqual([]);
});
test("privacy preview and mobile layout are usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page
    .getByRole("button", { name: "Missed Account privacy case" })
    .click();
  await expect(
    page.getByRole("link", { name: "Original PDF" }),
  ).toHaveAttribute("href", "privacy/original.pdf");
  await expect(page.locator("#previews img")).toBeVisible();
  expect(
    await page
      .locator("#previews img")
      .evaluate((image) => image.complete && image.naturalWidth > 0),
  ).toBe(true);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/privacy-mobile.png",
    fullPage: true,
  });
});
