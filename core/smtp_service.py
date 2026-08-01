import os
import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from core.models import AuditLog

logger = logging.getLogger(__name__)

def send_rescuer_email_alert(incident, custom_email=None, custom_notes=None):
    """
    Dispatches an emergency notification email to rescuer teams using SMTP.
    Configured via Django SMTP settings or environment variables:
    EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD.
    """
    recipient_email = custom_email or os.environ.get('RESCUER_ALERT_EMAIL', 'rescuer-team@eoc.gov.np')
    
    disaster = incident.disaster_type or "Disaster Emergency"
    location = incident.location_name or "Unknown Location"
    severity = incident.severity or 5
    score = incident.manual_priority if incident.manual_priority is not None else getattr(incident, 'triage_score', 85)
    lat = round(incident.lat, 4) if incident.lat else 0.0
    lng = round(incident.lng, 4) if incident.lng else 0.0

    subject = f"🚨 EMERGENCY DISPATCH ALERT: {disaster} at {location} (Priority Score: {score}/100)"

    text_body = (
        f"PRATHAMIKTA EOC EMERGENCY DISPATCH NOTIFICATION\n"
        f"=================================================\n\n"
        f"Incident ID: inc_{incident.id}\n"
        f"Hazard Type: {disaster}\n"
        f"Location: {location} (District: {incident.district_id})\n"
        f"GPS Coordinates: Lat {lat}, Lng {lng}\n"
        f"Severity: {severity}/10 | Priority Score: {score}/100\n"
        f"Life Threat Status: {'YES (URGENT)' if incident.is_life_threat else 'NO'}\n\n"
        f"Additional Dispatch Notes: {custom_notes or 'Immediate deployment of first responder units required.'}\n\n"
        f"Nepal MoHA National Emergency Operations Center (NEOC)"
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0b0f17; color: #f8fafc; padding: 20px; border-radius: 8px;">
        <h2 style="color: #ef4444; border-bottom: 2px solid #ef4444; padding-bottom: 8px; margin-top: 0;">
            🚨 PRATHAMIKTA EOC DISPATCH ALERT
        </h2>
        <p>An emergency situation requires immediate rescuer deployment:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <tr style="background: #1e2638;">
                <td style="padding: 8px; font-weight: bold; width: 35%;">Incident ID:</td>
                <td style="padding: 8px; color: #38bdf8;">inc_{incident.id}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">Hazard Type:</td>
                <td style="padding: 8px;">{disaster}</td>
            </tr>
            <tr style="background: #1e2638;">
                <td style="padding: 8px; font-weight: bold;">Location:</td>
                <td style="padding: 8px; color: #f97316;">{location} ({incident.district_id})</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">GPS Coordinates:</td>
                <td style="padding: 8px;">{lat}, {lng}</td>
            </tr>
            <tr style="background: #1e2638;">
                <td style="padding: 8px; font-weight: bold;">Priority Triage Score:</td>
                <td style="padding: 8px; color: #ef4444; font-weight: bold; font-size: 16px;">{score} / 100</td>
            </tr>
        </table>
        
        <div style="background: #172032; padding: 12px; border-left: 4px solid #38bdf8; margin-top: 15px;">
            <strong>Dispatcher Notes:</strong> {custom_notes or 'Immediate deployment of first responder units required.'}
        </div>
        
        <p style="font-size: 11px; color: #94a3b8; margin-top: 20px;">
            MoHA National Emergency Operations Center • Kathmandu, Nepal
        </p>
    </div>
    """

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '') or 'eoc-dispatch@prathamikta.gov.np'
    sent_status = "Dispatched via SMTP Email"
    error_msg = None

    # Check if credentials are missing
    host_user = getattr(settings, 'EMAIL_HOST_USER', '')
    host_pass = getattr(settings, 'EMAIL_HOST_PASSWORD', '')

    if not host_user or not host_pass:
        error_msg = (
            "SMTP Credentials missing! Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD "
            "in ndifts/settings.py or environment variables."
        )
        sent_status = f"Failed ({error_msg})"
        logger.warning(error_msg)
    else:
        try:
            msg = EmailMultiAlternatives(subject, text_body, from_email, [recipient_email])
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)
            logger.info(f"SMTP Email alert successfully sent to {recipient_email} for incident {incident.id}")
            sent_status = "Successfully Delivered via SMTP"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"SMTP Email dispatch error: {e}")
            sent_status = f"Failed ({e})"

    # Log dispatch in AuditLog
    audit_text = f"📧 SMTP EMAIL DISPATCH: Sent to rescuer {recipient_email} (Status: {sent_status})"
    AuditLog.objects.create(incident=incident, message=audit_text)

    return {
        'success': error_msg is None,
        'incident_id': incident.id,
        'recipient': recipient_email,
        'status': sent_status,
        'error': error_msg
    }
