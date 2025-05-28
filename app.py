from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from werkzeug.utils import secure_filename
import os
import datetime
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = 'alpha_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/upload-logo', methods=['POST'])
def upload_logo():
    if 'logo' not in request.files:
        flash('No file part')
        return redirect(url_for('home'))
    file = request.files['logo']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('home'))
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    flash('Logo uploaded successfully')
    return redirect(url_for('home'))

@app.route('/generate', methods=['POST'])
def generate():
    client = request.form['client']
    email = request.form.get('email')
    logo_path = request.form.get('logo_path')
    items = []
    for i in range(1, 6):
        name = request.form.get(f'name{i}')
        desc = request.form.get(f'desc{i}')
        qty = request.form.get(f'qty{i}')
        price = request.form.get(f'price{i}')
        if name and qty and price:
            items.append({
                'name': name,
                'desc': desc,
                'qty': int(qty),
                'price': float(price),
                'total': int(qty) * float(price)
            })

    total_amount = sum(item['total'] for item in items)
    vat = total_amount * 0.05
    grand_total = total_amount + vat

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    if logo_path and os.path.exists(logo_path):
        try:
            p.drawImage(logo_path, 50, height - 100, width=100, preserveAspectRatio=True, mask='auto')
        except:
            pass

    p.setFont("Helvetica-Bold", 14)
    p.drawString(200, height - 50, f"Quotation - ALPHA Kitchen")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 120, f"Client: {client}")
    p.drawString(50, height - 140, f"Date: {datetime.date.today().strftime('%Y-%m-%d')}")

    y = height - 180
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Item")
    p.drawString(200, y, "Description")
    p.drawString(350, y, "Qty")
    p.drawString(400, y, "Price")
    p.drawString(470, y, "Total")

    y -= 20
    p.setFont("Helvetica", 11)
    for item in items:
        p.drawString(50, y, item['name'])
        p.drawString(200, y, item['desc'])
        p.drawString(350, y, str(item['qty']))
        p.drawString(400, y, f"{item['price']:.2f}")
        p.drawString(470, y, f"{item['total']:.2f}")
        y -= 20

    y -= 20
    p.drawString(400, y, "Sub-total:")
    p.drawString(470, y, f"{total_amount:.2f}")
    y -= 20
    p.drawString(400, y, "VAT (5%):")
    p.drawString(470, y, f"{vat:.2f}")
    y -= 20
    p.drawString(400, y, "Grand Total:")
    p.drawString(470, y, f"{grand_total:.2f}")

    p.showPage()
    p.save()
    buffer.seek(0)

    if email:
        msg = EmailMessage()
        msg['Subject'] = 'Quotation from ALPHA Kitchen'
        msg['From'] = 'your-email@example.com'
        msg['To'] = email
        msg.set_content('Dear customer, please find attached your quotation.')

        msg.add_attachment(buffer.read(), maintype='application', subtype='pdf', filename='quotation.pdf')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('your-email@example.com', 'your-app-password')
            smtp.send_message(msg)

        flash('Quotation sent successfully via email.')
        return redirect(url_for('home'))

    return send_file(buffer, as_attachment=True, download_name="quotation.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
