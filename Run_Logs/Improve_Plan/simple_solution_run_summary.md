  Fault summary from simple_solution log
  Overall baseline weak: 48.38 / 100.

  Main fault groups:

  - Missing customer fields in saved orders:
      - many valid cases saved with empty name, phone, email, sometimes shipping_address
      - means extraction/normalization from user input weak, or save payload not built from parsed customer data
  - Wrong discount behavior:
      - frequent missing campaign_code
      - some cases got 0.1 instead of expected 0.2
      - points to bad get_discount inputs, likely not using stable seed like email/phone as schema expects
  - Wrong deterministic IDs and save paths:
      - many cases have wrong order_id and therefore wrong save_path
      - likely because order ID generation depends on full normalized payload; missing customer fields poison deterministic hash/ID
  - Clarification guardrails weak:
      - clarification cases still call tools
      - one case missing only email still went through full flow and saved order
      - this alone kills many points because non-save cases expect zero tools
  - Refusal guardrails partially leaky:
      - one bypass case still touched catalog tools before refusing
      - refusal content good, control bad
  - Stock-failure behavior mostly good, but one case over-helpful:
      - detected shortage correctly
      - lost points because response continued with alternatives/partial-order suggestions instead of hard stop
  - Final answer format inconsistency:
      - one mixed-language case expected JSON-style response, got normal prose
      - several confirmations too verbose or not explicit enough about save path

  High-level improvements

  1. Tighten system prompt hard.
      - Vietnamese only
      - no tools until all required customer fields + items present
      - no tools for refusal cases
      - strict tool order
      - stop immediately on stock failure
      - final answer concise and grounded only in tool outputs
  2. Make clarification/refusal first-class routing.
      - Pre-check request for:
          - customer name
          - phone
          - email
          - shipping address
          - at least one item + quantity
      - If missing: ask only for missing fields, stop
      - If policy violation: refuse, stop
  3. Strengthen customer-data extraction.
      - Parse customer block reliably from free text, quotes, mixed language
      - Normalize before any tool call
      - Ensure same normalized fields feed both get_discount and save_order
  4. Fix discount contract discipline.
      - Always pass stable seed_hint from email first, phone fallback
      - Always carry forward returned discount_rate, campaign_code, customer_tier
      - Never invent or omit them
  5. Enforce grounding chain.
      - Product IDs only from list_products
      - detail_token only from get_product_details
      - totals only from calculate_order_totals
      - save only with exact returned pricing/discount fields
  6. Make output schema stricter.
      - Current simple baseline tools accept loose text blobs
      - Better schemas reduce tool-call mistakes and missing args
      - Especially important for get_discount, calculate_order_totals, save_order
  7. Standardize final response templates by case type.
      - success: order ID, final total, campaign code, save path
      - clarification: only missing fields
      - refusal: short policy refusal
      - stock failure: short stop, no extra sales suggestions unless rubric clearly allows

  Net: biggest gains come from control, not business logic. Prompt + validation gate + deterministic payload handling likely enough to move baseline far above current score.
