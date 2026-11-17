# Setup and limitations

## n8n workflows

Import the five JSON files in `workflows/` into a compatible n8n instance. They are organized by agent number and intentionally have no saved credential bindings. Before running:

1. Create your own API and model credentials in n8n. Never commit their values.
2. Point HTTP Request nodes at your authorized simulator bridge (the example local endpoint is `http://127.0.0.1:8000`).
3. Re-select the imported subworkflows in Agent 1's Execute Workflow nodes. Original n8n workflow IDs are instance-specific.
4. In Agent 3's configuration Code node, replace `REPLACE_WITH_BRIDGE_API_KEY` with a value **only in your local n8n instance**. The exported portfolio copy must remain a placeholder. Prefer retrieving secrets through a protected n8n credential or another locally approved secret-management method.
5. Verify the simulator's current tool schema, approval policy, and test conditions before allowing any purchase-order or message-sending step.

Some exports contain temporary local test nodes and reference competition-specific tool endpoints. The repository demonstrates the architecture; it is **not a ready-to-run package without the original simulator environment**.

## Dashboard

The dashboard includes three saved practice scenarios (24 monitoring cycles each), extracted from actual competition practice outputs. Select these to review the timeline and five-agent decisions without an API key. Live mode requires a separately running, authorized bridge and an API key supplied at runtime.

The scenarios include order creation, delayed supply, suspicious supplier messages, and cases requiring human review. Values represent simulated business exposure and should not be interpreted as real-world savings.

## Security and publishing

- Exported n8n credential bindings, instance metadata, and temporary public tunnel addresses were removed.
- A hard-coded competition bridge key found in Agent 3's original export was replaced by a placeholder. **Rotate/revoke the original key if the bridge or tunnel could still accept it.**
- Never upload actual customer/supplier records, API secrets, private spreadsheets, or unapproved competition simulator material.
- Consult the team and organizers about permission before making competition-origin code/data public; keep this repository private in the meantime.
