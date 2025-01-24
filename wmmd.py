import csv
import re
import io
from flask import Flask, render_template, request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def mail():
    return render_template("wmmd.html", valid_emails=[], invalid_emails=[], csv_filename=None)

@app.route('/upload', methods=['POST'])
def upload():
    csvFile = request.files['csvFile']
    filename = csvFile.filename
    
    if csvFile:
        csvFile.save(filename)
        
        invalid_emails = get_invalid_emails(filename)
        valid_emails = get_valid_emails(filename)

        invalid_emails.sort()
        valid_emails.sort()

        return render_template("wmmd.html", invalid_emails=invalid_emails, valid_emails=valid_emails, csv_filename=filename)
        
    return render_template("wmmd.html", valid_emails=[], invalid_emails=[], csv_filename=None)

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) 

def get_invalid_emails(csvFile):
    invalid_emails = []
    with open(csvFile, 'r', encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            email = row[0]
            if not is_valid_email(email):
                invalid_emails.append(email)
    return invalid_emails

def get_valid_emails(csvFile):
    valid_emails = []
    with open(csvFile, 'r', encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            email = row[0]
            if is_valid_email(email):
                valid_emails.append(email)
    return valid_emails

def generate_csv(emails):
    output = io.StringIO()
    writer = csv.writer(output)

    for email in emails:
        writer.writerow([email])

    return output.getvalue()

@app.route('/send-emails', methods=['POST'])
def send_emails():
    csv_filename = request.form['csvFilename']
    email_user = request.form['emailUser']
    email_password = request.form['emailPassword']
    email_subject = request.form['emailSubject']
    email_body = request.form['emailBody']

    valid_emails = get_valid_emails(csv_filename)
    email_attachment = request.files.get('emailAttachment')  # Get the media attachment file if provided
    send_mail(valid_emails, email_user, email_password, email_subject, email_body, email_attachment)

    return "Emails sent successfully!"

def send_mail(emails, email_user, email_password, email_subject, email_body, email_attachment=None):
    for email_target in emails:
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email_target
        msg['Subject'] = email_subject

        msg.attach(MIMEText(email_body))
        
        if email_attachment:
            attached_file = MIMEApplication(email_attachment.read(), Name=email_attachment.filename)
            attached_file['Content-Disposition'] = f'attachment; filename="{email_attachment.filename}"'
            msg.attach(attached_file)

        text = msg.as_string()
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Change accordingly
        server.starttls()
        server.login(email_user, email_password)
        server.sendmail(email_user, email_target, text)
        server.quit()

if __name__ == "__main__":
    app.run()
