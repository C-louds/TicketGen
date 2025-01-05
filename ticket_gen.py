import os
import uuid
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.pagesizes import A4

# Set up directories
output_base_dir = "tickets"
os.makedirs(output_base_dir, exist_ok=True)

# Ticket template (replace this path with your actual ticket template image)
template_path = "ticket_template.png"
template_size = (800, 400)
if not os.path.exists(template_path):
    # Create a blank ticket template if none exists
    template = Image.new("RGB", template_size, "white")
    template.save(template_path)

# Font setup (use a system font or include your own)
font_path = "res/DejaVuSans-Bold.ttf"
font = ImageFont.truetype(font_path, 20)
font1 = ImageFont.truetype("res/TelegrafRegular.otf",15) 
font2 = ImageFont.truetype("res/DMSans-Bold.ttf",22)

# Function to generate QR code
def generate_qr(data, qr_file):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(qr_file)

# Function to create a ticket
def create_ticket(buyer_data, ticket_id, output_file, qr_file):
    ticket = Image.open(template_path)
    draw = ImageDraw.Draw(ticket)

    # Add details to ticket
    draw.text((1380+250, 475), f"{buyer_data['Name'].upper()}", fill="black", font=font2)
    draw.text((1380+255, 360), f"{ticket_id}", fill="black", font=font1)

    # Add QR code to ticket
    qr_code = Image.open(qr_file).resize((300, 300))
    ticket.paste(qr_code, (1380+265, 30))

    ticket_dir = os.path.join(output_base_dir, f"{buyer_data['Name'].upper().replace(' ', '_')}_{ticket_id}")
    os.makedirs(ticket_dir, exist_ok=True)

    # Save the ticket
    path1 = f"{ticket_dir}/{buyer_data['Name'].upper().replace(' ', '_')}_Ticket.png"
    ticket.save(path1)
    pdf_path = os.path.join(ticket_dir, f"{buyer_data['Name'].upper().replace(' ', '_')}_{ticket_id}.pdf")
    create_pdf(path1, qr_file, pdf_path)

def create_pdf(ticket_image_path, qr_file, pdf_path):
    """
    Generates a PDF that includes a ticket and its corresponding QR code.

    Args:
        ticket_image_path (str): Path to the ticket image.
        qr_file (str): Path to the QR code image.
        pdf_path (str): Output path for the PDF.
    """
    try:
        # Set up PDF canvas with A4 page size
        c = canvas.Canvas(pdf_path, pagesize=A4)
        page_width, page_height = A4

        # Calculate dynamic dimensions for images
        ticket_width = page_width * 0.8  # Scale ticket image to 80% of page width
        ticket_height = ticket_width * 0.4  # Maintain aspect ratio
        qr_size = ticket_height  # Make QR code square and proportional to ticket height

        # Draw ticket image (centered horizontally)
        ticket_x = (page_width - ticket_width) / 2
        ticket_y = page_height - ticket_height - 50  # Top margin of 50
        c.drawImage(ticket_image_path, ticket_x, ticket_y, width=ticket_width, height=ticket_height)

        # Draw QR code (centered horizontally below ticket)
        qr_x = (page_width - qr_size) / 2
        qr_y = ticket_y - qr_size - 30  # Space of 30 between ticket and QR code
        c.drawImage(qr_file, qr_x, qr_y, width=qr_size, height=qr_size)

        # Add additional text (optional)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 50, "This ticket is valid for the event. Please present this at the entry.")

        # Finalize the PDF
        c.save()

    except Exception as e:
        print(f"Error generating PDF: {e}")

# Main script to process data
def process_csv_and_generate_tickets(csv_file):
    # Load the CSV data
    data = pd.read_csv(csv_file)
    data.columns = data.columns.str.replace('\n', ' ').str.strip()
    data.fillna("", inplace=True)

    # Key columns
    contact_col = "Contact (You will receive your tickets on this contact)"

    for index, row in data.iterrows():
        group_size = int(row["Group Size"])
        if group_size == 1:
            # Single ticket
            ticket_id = str(uuid.uuid4())
            qr_data = (
                f"Name: {row['Full Name']}, Timestamp: {row['Timestamp']}, "
                f"Gender: {row['Gender']}, Contact: {row[contact_col]}, "
                f"Standard: {row['Standard']}",
            )
            qr_file = os.path.join(output_base_dir, f"qr_{ticket_id}.png")  # Specify the correct directory
            generate_qr(qr_data, qr_file)
            output_file = os.path.join(output_base_dir, f"ticket_{ticket_id}.png")  # Specify the correct directory
            create_ticket({
                "Name": row["Full Name"],
                "Standard": row["Standard"]
            }, ticket_id, output_file, qr_file)
        elif group_size in [5, 10]:
            # Group tickets
            for i in range(1, group_size + 1):
                guest_name_col = f"Guest {i} Name"
                guest_contact_col = f"Guest {i} Contact (You will receive your tickets on this contact)"
                guest_gender_col = f"Guest {i} Gender"
                if row[guest_name_col]:
                    ticket_id = str(uuid.uuid4())
                    qr_data = (
                        f"Group Timestamp: {row['Timestamp']}, Standard: {row['Standard']}, "
                        f"School: {row['School']}, Guest Name: {row[guest_name_col]}, "
                        f"Guest Contact: {row[guest_contact_col]}, Guest Gender: {row[guest_gender_col]}"
                    )
                    qr_file = os.path.join(output_base_dir, f"qr_{ticket_id}.png")  # Specify the correct directory
                    generate_qr(qr_data, qr_file)
                    output_file = os.path.join(output_base_dir, f"ticket_{ticket_id}.png")  # Specify the correct directory
                    create_ticket({
                        "Name": row[guest_name_col],
                        "Standard": row["Standard"]
                    }, ticket_id, output_file, qr_file)

# Run the script
if __name__ == "__main__":
    csv_file = "Event_Registration.csv"
    process_csv_and_generate_tickets(csv_file)