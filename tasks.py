from robocorp import browser
from robocorp.tasks import task
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
import time


@task
def order_robots_from_robot_spare_bin():
    configure_browser()
    navigate_to_robot_order_website()
    download_order_csv()
    table = load_order_data()
    process_orders(table)
    zip_receipts()

def configure_browser():
    browser.configure(browser_engine="msedge")

def navigate_to_robot_order_website():
    page = browser.page()
    page.goto('https://robotsparebinindustries.com/#/robot-order')
    time.sleep(3)  # Wait for the page to load

def download_order_csv():
    http = HTTP()
    http.download('https://robotsparebinindustries.com/orders.csv', overwrite=True)

def load_order_data():
    tables = Tables()
    return tables.read_table_from_csv(path="./orders.csv", header=True)

def process_orders(orders):
    for order in orders:
        populate_order_form(order)

def populate_order_form(order):
    page = browser.page()
    acknowledge_dialog()
    
    body_part_number = order["Body"]
    order_number = order["Order number"]
    head_part_number = order["Head"]
    legs_part_number = order["Legs"]
    address = order["Address"]
    
    print(body_part_number, order_number, head_part_number, legs_part_number)
    
    page.select_option("#head", value=head_part_number)
    page.click(f"#id-body-{body_part_number}")
    page.fill("input.form-control[type='number'][placeholder='Enter the part number for the legs']", legs_part_number)
    page.fill("#address", address)
    submit_order()
    order_id = retrieve_order_id()
    receipt_pdf_path = generate_receipt_pdf(order_id)
    robot_image_path = capture_robot_image(order_id)
    embed_image_in_pdf(robot_image_path, receipt_pdf_path)
    initiate_new_order()

def acknowledge_dialog():
    try:
        browser.page().click("text=OK")
    except Exception as e:
        print(f"Error clicking OK button: {e}")

def submit_order():
    page = browser.page()
    page.click("#order")
    if not page.is_visible("#receipt"):
        page.click("#order")  # Retry if receipt is not immediately visible

def generate_receipt_pdf(order_id):
    pdf = PDF()
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()
    receipt_pdf_path = f"output/orders/{order_id}.pdf"
    pdf.html_to_pdf(receipt_html, receipt_pdf_path)
    return receipt_pdf_path

def retrieve_order_id():
    return browser.page().locator(".badge.badge-success").inner_text()

def capture_robot_image(order_id):
    page = browser.page()
    image_path = f"output/images/{order_id}.jpeg"
    page.locator("#robot-preview-image").screenshot(path=image_path)
    return image_path

def embed_image_in_pdf(image_path, pdf_path):
    pdf = PDF()
    pdf.add_watermark_image_to_pdf(image_path=image_path, source_path=pdf_path, output_path=pdf_path)

def initiate_new_order():
    browser.page().click("#order-another")

def zip_receipts():
    archive = Archive()
    archive.archive_folder_with_zip("./output/orders", "./output/receipts.zip")