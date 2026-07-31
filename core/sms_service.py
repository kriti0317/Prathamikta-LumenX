import os
import re
import logging
import requests
from django.utils import timezone
from core.models import AuditLog

logger = logging.getLogger(__name__)

def send_disaster_sms_alert(incident, custom_phone=None):
    """
    Dispatches SMS emergency alert using Sparrow SMS Nepal API.
    Primary gateway for Nepal telecom cellular networks (NTC / Ncell).
    """
    raw_recipient = custom_phone or os.environ.get('ALERT_RECIPIENT_PHONE', '9864265886')

    
    # Format Nepal mobile number (extract 10-digit number like 98XXXXXX or 97XXXXXX)
    clean_digits = re.sub(r'\D', '', str(raw_recipient))
    if len(clean_digits) > 10 and clean_digits.startswith('977'):
        mobile_number = clean_digits[3:]
    else:
        mobile_number = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits

    disaster = incident.disaster_type or "Disaster Emergency"
    location = incident.location_name or "Unknown Location"
    severity = incident.severity or 5
    lat = round(incident.lat, 4) if incident.lat else 0.0
    lng = round(incident.lng, 4) if incident.lng else 0.0

    message_body = (
        f"🚨 PRATHAMIKTA EOC ALERT: New {disaster} logged at {location}! "
        f"Severity: {severity}/10. Coordinates: ({lat}, {lng}). "
        f"Immediate dispatch required."
    )

    mode = "simulated"
    sent_status = "Dispatched (Simulated Sparrow SMS Gateway)"
    error_msg = None

    sparrow_token = os.environ.get('SPARROW_SMS_TOKEN')
    sparrow_identity = os.environ.get('SPARROW_SMS_IDENTITY', 'Demo')

    # 1. Sparrow SMS Nepal API Integration
    if sparrow_token:
        try:
            sparrow_url = "http://api.sparrowsms.com/v2/sms/"
            params = {
                'token': sparrow_token,
                'from': sparrow_identity,
                'to': mobile_number,
                'text': message_body
            }
            res = requests.get(sparrow_url, params=params, timeout=8.0)
            if res.status_code == 200:
                res_data = res.json() if res.headers.get('content-type', '').startswith('application/json') else {'response': res.text}
                mode = "sparrow_sms"
                sent_status = f"Dispatched via Sparrow SMS Nepal (Response Code: {res.status_code}, Payload: {res.text})"
            else:
                error_msg = f"Sparrow SMS API Error (HTTP {res.status_code}): {res.text}"
                sent_status = f"Failed ({error_msg})"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Sparrow SMS dispatch error: {e}")
            sent_status = f"Failed (Sparrow SMS Exception: {e})"

    # 2. Twilio Gateway Fallback if configured
    else:
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        from_phone = os.environ.get('TWILIO_PHONE_NUMBER', '+18005550199')

        if account_sid and auth_token:
            try:
                from twilio.rest import Client
                client = Client(account_sid, auth_token)
                full_recipient = f"+977{mobile_number}" if not raw_recipient.startswith('+') else raw_recipient
                message = client.messages.create(
                    body=message_body,
                    from_=from_phone,
                    to=full_recipient
                )
                mode = "twilio"
                sent_status = f"Dispatched via Twilio Gateway (SID: {message.sid})"
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Twilio SMS dispatch failed: {e}")
                sent_status = f"Failed (Twilio Error: {e})"

    # Log dispatch to system AuditLog
    display_phone = f"+977{mobile_number}" if len(mobile_number) == 10 else mobile_number
    audit_text = f"📱 SMS ALERT [{mode.upper()}]: '{message_body}' -> Recipient: {display_phone} ({sent_status})"
    AuditLog.objects.create(incident=incident, message=audit_text)

    return {
        'success': error_msg is None,
        'mode': mode,
        'incident_id': incident.id,
        'recipient': display_phone,
        'mobile_number': mobile_number,
        'message': message_body,
        'status': sent_status,
        'error': error_msg
    }
