 Main gaps:

  1. workstation_bundle_mixed_language

  - only real fault left
  - feedback says:
      - mixed-language parsing good
      - catalog mapping good
      - total shown in final answer wrong
      - response did not include exact expected JSON-style content
  - meaning:
      - saved flow likely mostly correct
      - last-mile answer composition still drifted from tool output, or answer format too free

  2. executive_dual_monitor_bundle

  - tiny answer-quality leak
  - confirmation omitted delivery address and email
  - added extra details not requested

  High-level improvements:

  1. Make final answer fully template-driven

  - success answer should be built from saved payload only
  - no recomputing totals in prose
  - no reformatted number from model memory
  - pull order_id, final_total, campaign_code, save_path, customer fields directly from saved_order

  2. Standardize one success-response schema

  - same field order every time
  - same minimal content every time
  - especially for mixed-language case, remove free-form variation
  - if rubric sometimes wants JSON-like output, consider one stable structured format for all success cases

  3. Reduce answer creativity after tools finish

  - once save_order succeeds, model should switch to “report mode”
  - no extra interpretation
  - no extra product math
  - no omitted customer fields if confirmation should include them

  4. Add stronger “final answer grounding” rule to prompt

  - “After save_order, final answer must use only saved_order values”
  - “Do not restate totals unless copied from saved payload”
  - “Do not omit customer fields when they are part of confirmation context”

  5. If needed, add post-processing formatter in code

  - strongest fix
  - instead of trusting model for final success message, generate response string from saved_order
  - this removes residual drift in totals / formatting

  Best next move:

  - implement deterministic final success formatter from saved_order
  - keep model for clarification/refusal/error cases
  - use formatter for success cases only

  That likely removes last 0.46 points.

