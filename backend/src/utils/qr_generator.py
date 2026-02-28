import base64
import logging

logger = logging.getLogger(__name__)

def generate_upi_qr_data_uri(amount: float, order_id: str) -> str:
    """
    Generates a mock UPI QR code as a Base64-encoded SVG data URI.
    Format: upi://pay?pa=medisync@upi&pn=MediSync&am={amount}&cu=INR&tn=Order{order_id}
    """
    upi_link = f"upi://pay?pa=medisync@upi&pn=MediSync&am={amount:.2f}&cu=INR&tn=Order_{order_id}"
    
    # Simple SVG template for a mock QR code (static pattern)
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
        <rect width="200" height="200" fill="#ffffff" />
        <rect x="20" y="20" width="40" height="40" fill="#000000" />
        <rect x="140" y="20" width="40" height="40" fill="#000000" />
        <rect x="20" y="140" width="40" height="40" fill="#000000" />
        <rect x="40" y="40" width="20" height="20" fill="#ffffff" />
        <rect x="140" y="40" width="20" height="20" fill="#ffffff" />
        <rect x="40" y="140" width="20" height="20" fill="#ffffff" />
        <rect x="70" y="70" width="60" height="60" fill="#d0d0d0" />
        <text x="100" y="190" font-family="monospace" font-size="8" text-anchor="middle" fill="#555555">SCAN TO PAY ₹{amount:.2f}</text>
        <rect x="80" y="80" width="10" height="10" fill="#000000" />
        <rect x="110" y="80" width="10" height="10" fill="#000000" />
        <rect x="80" y="110" width="10" height="10" fill="#000000" />
        <rect x="110" y="110" width="10" height="10" fill="#000000" />
    </svg>"""
    
    encoded = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{encoded}"
