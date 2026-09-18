export function appendReview(history, input, caseIds, timestamp) {
  if (!caseIds.includes(input.case_id)) throw new Error("Choose a known case.");
  if (!["accept", "revise", "needs-context"].includes(input.decision))
    throw new Error("Choose a review decision.");
  if (
    typeof input.evidence !== "string" ||
    input.evidence.trim().length < 10 ||
    input.evidence.length > 2000
  )
    throw new Error("Write 10–2000 characters of evidence.");
  return [
    ...history,
    {
      revision: history.length + 1,
      case_id: input.case_id,
      decision: input.decision,
      evidence: input.evidence.trim(),
      created_at: timestamp,
      classification: "human-review-of-synthetic-fixture",
    },
  ];
}
export function exportReviews(history) {
  return {
    schema_version: 1,
    classification: "synthetic",
    certification: false,
    history,
  };
}
