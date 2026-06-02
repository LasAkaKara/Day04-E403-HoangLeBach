# Prompt and Agent Loop Update 2

## Context

This was the second refinement of `src/agent/graph.py` after reviewing `Run_Logs/Improve_Plan/run_1_log.md`.

At that point the score was already strong, but two meaningful control gaps remained:
- `creator_premium_bundle_quotes`: the agent over-clarified and asked for quantity instead of creating the order
- `insufficient_stock_headphones`: the agent stopped after `list_products` instead of calling `get_product_details`

There was also one smaller issue:
- success confirmation did not explicitly reflect catalog/pricing workflow strongly enough in one case

## How the System Prompt Was Improved

### 1. Relaxed the quantity requirement for clearly named items
In the first prompt version, valid order creation still depended on having a product request with quantity.
That was too strict for this benchmark, because one case provided a fully specified product list but omitted explicit quantities.

The prompt was changed to say:
- if a product name is clear but quantity is missing, default quantity to `1`

This directly addressed the `creator_premium_bundle_quotes` failure.

### 2. Treated quoted product names as valid item requests
The prompt was updated to explicitly recognize:
- product names inside quotes
- mixed English/Vietnamese item names

The new instruction said these still count as valid product requests and should not trigger clarification by themselves.

This addressed the root cause where the model saw quoted premium product names as incomplete item specs.

### 3. Narrowed when clarification is allowed
The earlier prompt already had clarification rules, but Update 2 tightened the boundary further.

The new prompt says clarification is allowed only when:
- required customer fields are missing
- product identity is truly ambiguous and cannot be mapped to the catalog

This was important because the problem in `creator_premium_bundle_quotes` was not missing customer data; it was over-cautious interpretation of already-valid item names.

### 4. Strengthened the stock-validation rule
The prompt was updated to explicitly say:
- do not conclude stock sufficiency or insufficiency from `list_products`
- after matching products, always call `get_product_details` before deciding about stock, price, or whether the order can proceed

This directly addressed `insufficient_stock_headphones`, where the model stopped too early.

### 5. Slightly strengthened success grounding
The success-format instruction was refined so the final answer should indicate:
- products were mapped from the catalog
- pricing/discount was calculated
- the order was saved

This targeted the small answer-quality loss in `office_workstation_bundle`.

## How the Agent Loop Was Improved

### 1. Added a runtime user-message wrapper
A new helper, `build_runtime_user_message(query)`, was added.

It wraps the original user query with a short execution reminder that reinforces the most fragile behaviors:
- default missing quantity to `1` for clearly named items
- quoted product names are valid requests
- call `get_product_details` before any stock conclusion
- ask clarification only for genuinely missing required customer fields or ambiguous product identity

This is effectively a second control layer on top of the system prompt.

### 2. Routed agent invocation through the wrapper
`run_agent()` was changed so the agent no longer receives the raw query directly.
Instead, it receives the wrapped message from `build_runtime_user_message(query)`.

This improved the agent loop because the high-risk instructions now sit immediately next to the user request at execution time, not only in the distant system prompt.

### 3. Targeted the exact remaining failure modes
Unlike Update 1, which addressed broad structural weakness, Update 2 was surgical.
It focused on:
- false clarification on quoted-item orders
- premature stock conclusion before details lookup
- slightly under-grounded success confirmations

That made the loop better aligned with the actual residual errors instead of reworking already-correct parts.

## Net Effect of Update 2

Update 2 did not rebuild the agent. It refined the control surface around the last two failure patterns.

At a high level, it improved the prompt and loop in three ways:
- more tolerant item interpretation when product names are clearly specified
- stricter enforcement of detail lookup before stock decisions
- stronger execution-time reminders for the exact mistakes still happening

In short:
- Update 1 made the agent controlled
- Update 2 made the agent less brittle on quoted-item parsing and more disciplined on stock-validation flow
