"""Remediation hints for known Google Ads mutate-blocking error codes.

Used by the Shared Budget Updater Slack alerts so an account-level policy
block arrives with the fix attached instead of a bare error code.
"""

ERROR_HINTS = {
    # EU TTPA enforcement: Google blocks ALL mutates on a customer that has
    # non-exempt campaigns without the EU political advertising declaration.
    # Not fixable in code — an admin declares once in the Google Ads UI.
    "EU_POLITICAL_ADVERTISING_DECLARATION_REQUIRED": (
        "Google is blocking ALL changes to this account until the EU political "
        "advertising declaration is completed. Open the account in the Google Ads "
        "UI (banner at the top, or Admin > Account settings > EU political "
        "advertising), submit the declaration, and this row will apply on the "
        "next run automatically."
    ),
}


def hint_for(error_code: str) -> str:
    """Return a remediation hint for a known error code, or '' if none."""
    return ERROR_HINTS.get(error_code, "")
