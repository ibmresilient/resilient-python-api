""" Send email via SMTP """

"""Send email"""

import os
import smtplib
import mimetypes
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def connect_smtp(user, password, server="smtp.office365.com", port=587):
    """Make a SMTP connection"""
    server = smtplib.SMTP(server, port)
    server.ehlo()
    server.starttls()
    server.login(user, password)
    return server


def connect_smtp_ssl(user, password, server="smtp.office365.com", port=465):
    """Make a SMTP connection directly over SSL. Legacy application usage."""
    server = smtplib.SMTP_SSL(server, port)
    server.ehlo()
    server.login(user, password)
    server.ehlo()
    return server


def connect_smtp_insecure(user, password, server="smtp.office365.com", port=25):
    """ Make an unencyripted, inscure SMTP connection """
    server = smtplib.SMTP(server, port)
    server.login(user, password)
    return server


def send_email(smtp, sender, recipients, subject, body, attachments):
    """Send email"""
    # Create the outer message.
    outer = MIMEMultipart()
    outer['Subject'] = subject

    if isinstance(recipients, list) or isinstance(recipients, tuple):
        recipients = ", ".join([str(recip) for recip in recipients])

    outer['To'] = recipients
    outer['From'] = sender

    msg = MIMEText(body, "plain")
    outer.attach(msg)

    if attachments is not None:
        for path in attachments:
            path = os.path.expanduser(path)
            if not os.path.isfile(path):
                continue
            filename = os.path.basename(path)
            # Guess the content type based on the file's extension.  Encoding
            # will be ignored, although we should check for simple things like
            # gzip'd or compressed files.
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            if maintype == 'text':
                fp = open(path)
                # Note: we should handle calculating the charset
                msg = MIMEText(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == 'image':
                fp = open(path, 'rb')
                msg = MIMEImage(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == 'audio':
                fp = open(path, 'rb')
                msg = MIMEAudio(fp.read(), _subtype=subtype)
                fp.close()
            else:
                fp = open(path, 'rb')
                msg = MIMEBase(maintype, subtype)
                msg.set_payload(fp.read())
                fp.close()
                # Encode the payload using Base64
                encoders.encode_base64(msg)
            # Set the filename parameter
            msg.add_header('Content-Disposition', 'attachment', filename=filename)
            outer.attach(msg)

    # Send the email via the configured SMTP server.
    smtp.sendmail(sender, recipients, outer.as_string())
    smtp.quit()


def test():
    import getpass
    #atts = ["data.xlsx", "~/resilient/cert.cer"]
    atts = None
    user = raw_input("Username: ")
    from_addr = "restester@yahoo.com"
    password = getpass.getpass("Password: ")
    smtp_server = 'smtp.mail.yahoo.com'
    server = connect_smtp(user, password, server=smtp_server)
    send_email(server, from_addr, ["user@example.com",], "From port 587", "test mail", atts)

    server = connect_smtp_ssl(user, password, server=smtp_server)
    send_email(server, from_addr, ["user@example.com",], "From port 465", "test mail", atts)

    server = connect_smtp_insecure(user, password, server=smtp_server)
    send_email(server, from_addr, ["user@example.com",], "From port 25", "test mail", atts)


if __name__ == "__main__":
    test()
