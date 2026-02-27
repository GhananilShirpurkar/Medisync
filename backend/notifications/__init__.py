"""
NOTIFICATIONS MODULE
====================
Clean notification service layer for MediSync.

Responsibilities:
- Send order confirmations
- Send digital bills (PDF)
- Send prescription summaries
- Send status updates

Architecture:
- Output channel only (no AI logic)
- Independent and reusable
- Graceful failure handling
- Does not block order flow
"""
