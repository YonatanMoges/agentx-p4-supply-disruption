from datetime import datetime
from p4_supply_api import SupplyAPI


def plan_response(api, part_id, shortage_qty, required_by):
    """
    Find purchasing options for a shortage and choose
    the cheapest option that arrives before required_by.
    """

    # Step 1: Get part information
    inventory_info = api.get_inventory(part_id)
    part = inventory_info["part"]

    preferred_supplier = part["preferred_supplier"]
    alternates_raw = part.get("qualified_alternates")

    # Handle empty / None / NaN alternate suppliers safely
    if (
        alternates_raw is None
        or str(alternates_raw).lower() in ["nan", "none", ""]
    ):
        alternates = []
    else:
        alternates = [
            supplier.strip()
            for supplier in str(alternates_raw).split(",")
            if supplier.strip()
        ]

    # Preferred supplier + qualified alternatives
    suppliers = [preferred_supplier] + alternates

    # Step 2: Request sea and air quotes from every valid supplier
    options = []

    for supplier_id in suppliers:
        for mode in ["sea", "air"]:
            try:
                quote = api.request_quote(
                    part_id=part_id,
                    supplier_id=supplier_id,
                    qty=shortage_qty,
                    mode=mode,
                )

                options.append(quote)

            except Exception as e:
                print(
                    f"Quote failed for supplier {supplier_id} "
                    f"using {mode}: {e}"
                )

    if not options:
        return {
            "status": "no_options",
            "selected_option": None,
            "all_options": [],
        }

    # Step 3: Convert deadline into a date
    required_date = datetime.fromisoformat(required_by).date()

    # Step 4: Keep only options that arrive before deadline
    valid_options = [
        option
        for option in options
        if option["earliest_arrival"] <= required_date
    ]

    # Step 5: If nothing arrives in time, choose fastest option
    if not valid_options:
        fastest = min(
            options,
            key=lambda option: option["earliest_arrival"]
        )

        return {
            "status": "late",
            "selected_option": fastest,
            "all_options": options,
        }

    # Step 6: Choose cheapest option that arrives in time
    best = min(
        valid_options,
        key=lambda option: option["total_aed"]
    )

    return {
        "status": "on_time",
        "selected_option": best,
        "all_options": options,
    }


def execute_response(api, plan):
    """
    Execute the selected procurement response:
    1. Draft PO
    2. Request approval if required
    3. Send PO to supplier
    """

    selected = plan.get("selected_option")

    if selected is None:
        return {
            "status": "not_executed",
            "reason": "No purchasing option was selected."
        }

    # Step 1: Draft the purchase order
    justification = (
        f"Purchase required for {selected['part_id']} "
        f"to address an expected production shortage. "
        f"Selected {selected['supplier_id']} using "
        f"{selected['mode']} shipping."
    )

    draft = api.draft_purchase_order(
        quote_id=selected["quote_id"],
        justification=justification,
    )

    print("\nDraft PO created:")
    print(draft)

    # Step 2: Request approval if PO is above AED 50,000
    if draft["approval_required"]:
        approval_message = (
            f"Approval requested for PO {draft['po_id']} "
            f"for {draft['qty']} units of {draft['part_id']}. "
            f"This purchase is required to reduce the risk "
            f"of production disruption."
        )

        approval = api.request_approval(
            po_id=draft["po_id"],
            message=approval_message,
        )

        print("\nApproval result:")
        print(approval)

        # Stop if approval is rejected
        if approval["decision"] != "approved":
            return {
                "status": "approval_rejected",
                "draft_po": draft,
                "approval": approval,
            }

    # Step 3: Get supplier profile to find trusted email domain
    supplier_profile = api.get_supplier_profile(
        selected["supplier_id"]
    )

    supplier_domain = supplier_profile["email_domain"]

    # The simulator validates the domain.
    supplier_email = f"procurement@{supplier_domain}"

    # Step 4: Send the PO
    email_result = api.send_email(
        to=supplier_email,
        subject=f"Purchase Order {draft['po_id']}",
        body=(
            f"Please find purchase order {draft['po_id']} "
            f"for {draft['qty']} units of {draft['part_id']}."
        ),
        po_id=draft["po_id"],
    )

    print("\nPO sent:")
    print(email_result)

    return {
        "status": "executed",
        "selected_option": selected,
        "draft_po": draft,
        "email_result": email_result,
    }


if __name__ == "__main__":

    # Load the official P4 practice environment
    api = SupplyAPI(
        "practice_01",
        data_xlsx="data/P4_Supply_Disruption_Data.xlsx"
    )

    # -----------------------------
    # Scope 1: Find best response
    # -----------------------------

    plan = plan_response(
        api=api,
        part_id="P001",
        shortage_qty=150,
        required_by="2026-09-15"
    )

    print("\nSelected plan:")
    print(plan)

    # -----------------------------
    # Scope 2: Execute the response
    # -----------------------------

    result = execute_response(
        api=api,
        plan=plan
    )

    print("\nFinal execution result:")
    print(result)

    # Show simulator summary
    print("\nRun summary:")
    print(api.run_summary())