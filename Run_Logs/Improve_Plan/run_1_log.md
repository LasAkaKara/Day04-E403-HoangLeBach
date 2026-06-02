# Run 1 Improvement Plan

## Score Snapshot

- Overall score: `90.77 / 100`
- Total earned: `1180 / 1300`
- Strong coverage on most normal, clarification, and guardrail cases.
- Main remaining losses come from 2 control errors and 1 minor answer-quality issue.

## Fault Summary

### 1. `creator_premium_bundle_quotes` failed badly

Observed faults:
- Missing `saved_order` payload
- No tool calls at all
- Agent asked for quantity instead of creating the order

Why this matters:
- This single case cost `92` points.
- It is not a business-logic failure. It is a parsing and decision failure.
- The query already contained all required customer fields and an item list, so clarification should not have happened.

Likely root cause:
- Agent interpreted quoted product names as incomplete item specs.
- Agent required explicit quantity even though natural-language list without quantities should default to `1` in this benchmark pattern.
- Current missing-info gate is too aggressive when items are presented as quoted names.

### 2. `insufficient_stock_headphones` missed expected tool flow

Observed faults:
- Expected tool subsequence: `list_products -> get_product_details`
- Actual trace: `list_products`
- Response still correctly refused save due to stock issue

Why this matters:
- Behavior was semantically reasonable, but grader expects stock failure to be grounded by exact product details.
- Agent likely inferred insufficiency too early from catalog summaries alone.

Likely root cause:
- `list_products` currently exposes enough stock information for the model to stop before `get_product_details`.
- Prompt does not strongly force `get_product_details` before any stock-based failure conclusion.

### 3. `office_workstation_bundle` lost minor LLM-judge points

Observed fault:
- Final answer did not explicitly mention catalog lookup / price retrieval.

Why this matters:
- JSON and tools were correct.
- This is small, but still indicates the success template can be tightened.

## What We Need To Consider More

### Item completeness policy
We need sharper distinction between:
- truly missing item information
- item names that are fully specified but omit quantity

Current logic seems to treat both the same in some cases. For this dataset, a bare item name in a final order request should likely map to quantity `1` unless the request is actually ambiguous.

### Quoted-item parsing
Quoted names are a high-signal pattern. They should increase confidence, not trigger clarification. We need to treat:
- `"MacBook Air M3 13"`
- `"Sony WH-1000XM5"`
- etc.
as valid product mentions ready for lookup.

### Tool-order discipline on stock failures
Even when stock shortage seems obvious, agent still needs to call `get_product_details` before final stock refusal if the rubric expects that path.

### Success response grounding
Confirmation can stay concise, but should more explicitly reflect workflow completion:
- catalog matched
- pricing/discount applied
- order saved

Not verbose. Just slightly more grounded.

## High-Level Improvements

### 1. Relax clarification rule for omitted quantities
If request includes a concrete item list with recognizable product names and no quantity is specified, default quantity to `1` instead of asking follow-up.

High-level prompt update:
- If an item is clearly identified but has no explicit quantity, assume quantity `1`.
- Ask clarification only when product identity itself is ambiguous.

### 2. Add explicit quoted-item instruction to system prompt
Prompt should state:
- product names inside quotes count as valid product requests
- quoted names should be looked up directly with tools
- do not ask for clarification just because items are quoted or in English

### 3. Strengthen mandatory stock-validation sequence
Prompt should explicitly state:
- do not conclude stock sufficiency or insufficiency from `list_products` alone
- after product matching, always call `get_product_details` before any stock-based decision

### 4. Consider trimming stock from `list_products` output
If needed, reduce temptation for the model to stop early by keeping `list_products` focused on matching candidates, while reserving authoritative stock validation for `get_product_details`.

This may improve tool-trace compliance on edge cases.

### 5. Tighten final success template
Success answer should consistently include:
- order saved
- order ID
- final total
- campaign code
- save path
- brief signal that catalog/pricing flow completed

A short template will reduce minor LLM-judge leakage.

## Suggested Next Changes

1. Update system prompt with two explicit rules:
   - missing quantity for a clearly named item => assume `1`
   - stock decisions require `get_product_details`
2. Revisit any pre-tool completeness logic so quoted-item bundles are treated as valid orders.
3. Optionally reduce `stock` prominence in `list_products` output if tool-order mismatch persists.
4. Standardize one success-response template for all valid save cases.

## Priority

Highest priority:
- Fix `creator_premium_bundle_quotes`

Second priority:
- Force `get_product_details` on stock-failure path

Low priority:
- Polish confirmation wording for small judge gains
