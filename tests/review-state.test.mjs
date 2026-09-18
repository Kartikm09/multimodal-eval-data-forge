import { test } from "node:test";
import assert from "node:assert/strict";
import {
  appendReview,
  exportReviews,
} from "../examples/business-review/review-state.mjs";
const input = {
  case_id: "reference",
  decision: "needs-context",
  evidence: "Demand is only an assumption.",
};
test("review saves append independently without changing previous history", () => {
  const original = [];
  const one = appendReview(
    original,
    input,
    ["reference"],
    "2026-09-18T00:00:00Z",
  );
  const two = appendReview(
    one,
    { ...input, decision: "revise" },
    ["reference"],
    "2026-09-18T00:00:01Z",
  );
  assert.equal(original.length, 0);
  assert.equal(one.length, 1);
  assert.equal(two.length, 2);
  assert.deepEqual(two[0], one[0]);
  assert.equal(exportReviews(two).certification, false);
  assert.equal(two[1].revision, 2);
});
test("unknown cases, invalid decisions and missing evidence are rejected", () => {
  for (const bad of [
    { ...input, case_id: "unknown" },
    { ...input, decision: "certified" },
    { ...input, evidence: " " },
    { ...input, evidence: "x".repeat(2001) },
  ])
    assert.throws(() => appendReview([], bad, ["reference"], "now"));
});
