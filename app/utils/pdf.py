import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from app.utils.logger import logger

INVOICE_DIR = "generated_files/invoices"

os.makedirs(INVOICE_DIR, exist_ok=True)


# generates a real order invoice pdf, given to the customer once an
# order is placed
def generate_order_invoice_pdf(
    order_id: int,
    order_number: str,
    customer_name: str,
    restaurant_name: str,
    items: list[dict],
    subtotal: str,
    delivery_fee: str,
    discount: str,
    tax: str,
    total_amount: str
) -> str:

    try:

        file_path = os.path.join(INVOICE_DIR, f"invoice_{order_id}.pdf")

        pdf = canvas.Canvas(file_path, pagesize=A4)

        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(1 * inch, 10.5 * inch, "Order Invoice")

        pdf.setFont("Helvetica", 12)

        header_lines = [
            f"Order Number: {order_number}",
            f"Customer: {customer_name}",
            f"Restaurant: {restaurant_name}"
        ]

        y_position = 9.8 * inch

        for line in header_lines:

            pdf.drawString(1 * inch, y_position, line)
            y_position -= 0.35 * inch

        y_position -= 0.2 * inch

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(1 * inch, y_position, "Items")
        y_position -= 0.3 * inch

        pdf.setFont("Helvetica", 11)

        for item in items:

            line = f"{item['quantity']} x {item['item_name']} - {item['price_at_order']}"
            pdf.drawString(1.2 * inch, y_position, line)
            y_position -= 0.3 * inch

        y_position -= 0.2 * inch

        pdf.setFont("Helvetica", 12)

        totals_lines = [
            f"Subtotal: {subtotal}",
            f"Delivery Fee: {delivery_fee}",
            f"Discount: -{discount}",
            f"Tax: {tax}",
        ]

        for line in totals_lines:

            pdf.drawString(1 * inch, y_position, line)
            y_position -= 0.3 * inch

        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(1 * inch, y_position, f"Total Amount: {total_amount}")

        pdf.save()

        logger.info(f"Order invoice PDF generated : {file_path}")

        return file_path

    except Exception as error:

        logger.error(f"Order invoice PDF generation failed for order {order_id} : {str(error)}")

        raise