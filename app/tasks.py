from app.celery_app import celery_app
from app.utils.email import send_email
from app.utils.logger import logger


@celery_app.task(name="app.tasks.send_email_task")
def send_email_task(to_email: str, subject: str, body: str, attachment_paths: list[str] | None = None) -> None:

    try:

        send_email(to_email=to_email, subject=subject, body=body, attachment_paths=attachment_paths)

        logger.info(f"Celery task - email sent to {to_email} : {subject}")

    except Exception as error:

        logger.error(f"Celery task - email failed to {to_email} : {str(error)}")


@celery_app.task(name="app.tasks.send_order_confirmation_email")
def send_order_confirmation_email(to_email: str, customer_name: str, order_number: str, invoice_path: str | None = None) -> None:

    body = f"Hi {customer_name},\n\nYour order #{order_number} has been placed successfully. Your invoice is attached."

    attachments = [invoice_path] if invoice_path else []

    send_email_task(to_email, "Order Confirmed", body, attachment_paths=attachments)


@celery_app.task(name="app.tasks.send_order_status_update_email")
def send_order_status_update_email(to_email: str, customer_name: str, order_number: str, new_status: str) -> None:

    body = f"Hi {customer_name},\n\nYour order #{order_number} is now: {new_status}."

    send_email_task(to_email, "Order Status Update", body)


@celery_app.task(name="app.tasks.send_delivery_assignment_email")
def send_delivery_assignment_email(to_email: str, customer_name: str, order_number: str, partner_name: str) -> None:

    body = f"Hi {customer_name},\n\n{partner_name} has been assigned to deliver your order #{order_number}."

    send_email_task(to_email, "Delivery Partner Assigned", body)


@celery_app.task(name="app.tasks.send_order_delivered_email")
def send_order_delivered_email(to_email: str, customer_name: str, order_number: str) -> None:

    body = f"Hi {customer_name},\n\nYour order #{order_number} has been delivered. Enjoy your meal!"

    send_email_task(to_email, "Order Delivered", body)


@celery_app.task(name="app.tasks.send_payment_success_email")
def send_payment_success_email(to_email: str, customer_name: str, amount: str, order_number: str) -> None:

    body = f"Hi {customer_name},\n\nWe've received your payment of {amount} for order #{order_number}."

    send_email_task(to_email, "Payment Successful", body)


@celery_app.task(name="app.tasks.send_refund_email")
def send_refund_email(to_email: str, customer_name: str, order_number: str, refund_amount: str) -> None:

    body = f"Hi {customer_name},\n\nYour refund of {refund_amount} for order #{order_number} has been processed."

    send_email_task(to_email, "Refund Processed", body)