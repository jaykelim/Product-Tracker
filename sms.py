import smtplib
from config import INFO

carriers = {
    'att':    '@mms.att.net',
    'tmobile': ' @tmomail.net',
    'verizon':  '@vtext.com',
    'sprint':   '@page.nextel.com'
}


def send(msg):
    # Replace the number with your own, or consider using an argument\dict for multiple people.
    to_number = INFO.PHONENUM+'{}'.format(carriers['att'])
    auth = (INFO.EMAIL, INFO.EMAILPASSWORD)

    # Establish a secure session with gmail's outgoing SMTP server using your gmail account
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(auth[0], auth[1])

    server.sendmail(auth[0], to_number, msg)
