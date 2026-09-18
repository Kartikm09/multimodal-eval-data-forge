# Synthetic business-review verification

Executed on 18 September 2026 before publication:

| Check | Result |
| --- | --- |
| Original generator suite | 3/3 passed before extension |
| Full Python suite | 19/19 passed; no skips |
| Actual artifact verification | Reference passes; both candidates rejected for their intended defect categories |
| Review-state tests | 2/2 passed |
| Playwright 1.61.1 Chromium | 2/2 passed in the official Linux browser environment |
| PDF privacy | Original preserved; sanitized copy has no known extracted-value leaks; public product text retained |
| Seeded privacy failures | Painted-only/missed/excessive removal detected; Unicode offsets and exact-span metrics checked |
| Dependency scan | No known advisories in the final pinned Python and npm sets on the execution date |

Python and Node checks ran with a fresh environment, no credentials, no network and only the project/runtime readable. Browser checks ran in a credential-free, network-disabled Linux container with this repository as the sole mount. The container had no Docker socket. Native macOS browser interaction worked, but its isolated download operation was canceled; successful export verification uses the Linux result, not that failed native run.

Actual DOCX pages, all six slides, three formula sheets and five privacy PDFs were rendered and visually inspected. Package/layout validation passed for the presentations with one expected outside-slide warning in candidate B. The checker also treats that warning as the seeded clipping issue. Office and LibreOffice can substitute fonts differently; this is not pixel-equivalence evidence across applications.

Independent code review identified non-finite arithmetic and missing claim declarations as possible false passes. Regression tests reproduced both before the checks were corrected. Another regression prevents metadata from relabeling stale report text as a current fact. Claim checks remain limited to the explicit synthetic schema and do not claim general semantic fact verification.

The committed [screenshots](screenshots/linux-arm64/environment.json) show actual browser state against synthetic inputs. Tests verify keyboard submission, focus, persisted revision history, real JSON download contents, an empty search result and a mobile privacy preview. No hosted deployment, external reviewer acceptance, paid work, model accuracy or legal certification is claimed.

## Interview questions tied to this implementation

1. Why does `evaluate_formula` read formulas rather than cached XLSX values, and how does its independent source oracle reject an addition formula?
2. How can NaN produce a false pass in a tolerance comparison, and which tests guard both direct and computed non-finite values?
3. How do required claim coverage, exact text presence and claim metadata checks differ from general factual or writing-quality assessment?
4. Why does `painted-only.pdf` fail while the rebuilt text-only PDF passes, and which original PDF features are explicitly unsupported?
5. How do Unicode normalization and original-text offsets interact with exact-span precision/recall, and why does the ambiguous review case remain unscored?
