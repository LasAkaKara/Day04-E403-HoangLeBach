# Prompt and Agent Loop Update 1

## Context

This was the first major rewrite of `src/agent/graph.py` after reviewing the weak baseline and the early fault pattern.

Main problems being addressed:
- agent saved orders with missing customer fields
- agent sometimes called tools in clarification and refusal cases
- agent invented or dropped discount fields
- agent did not have a strict enough workflow for valid orders
- final confirmations were not consistently grounded in tool outputs

## How the System Prompt Was Improved

### 1. Made the task explicit
The original baseline prompt was vague: it only said to help make an order, check products, then pricing, then save.

The new prompt changed that into a strict order-agent instruction set:
- valid order creation
- clarification when required information is missing
- refusal for policy-violating requests
- failure response for stock or validation errors

This reduced model freedom and made the intended behavior much more concrete.

### 2. Added hard pre-tool validation rules
The new prompt explicitly required these fields before any tool call:
- customer name
- phone number
- email
- shipping address
- at least one product request with quantity

It also explicitly said:
- if anything is missing, ask for the missing fields and stop
- do not call tools before clarification is complete

This directly addressed the earlier failures where the model created or simulated orders with missing customer information.

### 3. Added strong refusal rules
The prompt was updated to refuse, without tools:
- fake invoices
- manual discount overrides
- stock bypass requests
- catalog/policy bypass requests

This addressed the earlier guardrail leak where the model sometimes touched tools before refusing.

### 4. Enforced exact tool order
The prompt now required the valid-order workflow:
1. `list_products`
2. `get_product_details`
3. `get_discount`
4. `calculate_order_totals`
5. `save_order`

It also said:
- do not skip steps
- do not reorder steps
- do not repeat tools unnecessarily

This addressed the rubric requirement that valid orders follow a deterministic trace.

### 5. Enforced grounding of critical fields
The prompt was updated to say the model must not invent:
- product IDs
- prices
- stock
- discount rate
- campaign code
- totals
- order ID
- save path

It also required:
- `product_id` only from `list_products`
- `detail_token` only from `get_product_details`
- `discount_rate` and `campaign_code` only from `get_discount`

This addressed the earlier faults where saved JSON had wrong discount fields, wrong IDs, and wrong paths.

### 6. Tightened stop conditions
The prompt explicitly said:
- no save if pricing validation fails
- no save if stock is insufficient
- no save if token or product validation fails
- stop after the error and reply concisely

This directly targeted the stock-failure cases.

### 7. Standardized the final answer goal
The prompt made the final answer concise and Vietnamese-only.
For success, it required:
- order ID
- final total
- campaign code
- save path

This addressed answer-quality leakage in the judge rubric.

## How the Agent Loop Was Improved

### 1. Replaced stubs with a real runnable loop
The file originally had TODO stubs for:
- `build_agent()`
- `run_agent()`
- final answer extraction
- tool trace extraction
- saved order extraction

These were all implemented.

### 2. Built a deterministic agent path
`build_agent()` now:
- creates `OrderDataStore`
- builds the chat model with `build_chat_model(...)`
- builds the five tools
- returns `create_agent(...)` with the strengthened system prompt

This gave the repo a real ReAct-style tool-using loop instead of a template.

### 3. Preserved tool traces for grading
`run_agent()` was implemented to:
- invoke the agent
- collect all messages
- extract tool calls and outputs
- extract the saved order payload if `save_order` ran
- return a complete `AgentResult`

This was necessary for the grader to verify tool order and saved JSON.

### 4. Kept tool schemas strict
The loop kept the Pydantic-backed tool schemas from `src/core/schemas.py`.
That improved argument discipline compared with the weak baseline, which used loose text inputs.

## Net Effect of Update 1

This first rewrite addressed the large structural problems:
- vague behavior control
- weak clarification logic
- weak refusal logic
- tool-order looseness
- ungrounded outputs
- missing grading hooks

At a high level, Update 1 turned the agent from a loosely instructed assistant into a rubric-driven order workflow.
