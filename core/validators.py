import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_no_html_tags(value):
    if re.search(r'<[^>]+>', str(value)):
        raise ValidationError(_('No se permiten etiquetas HTML.'))


def validate_phone_peru(value):
    if value and not re.match(r'^9\d{8}$', str(value)):
        raise ValidationError(_('Teléfono inválido. Formato: 9XXXXXXXX'))


def validate_strong_password_extra(value):
    if not re.search(r'[A-Z]', value):
        raise ValidationError(_('Debe contener al menos una mayúscula.'))
    if not re.search(r'\d', value):
        raise ValidationError(_('Debe contener al menos un número.'))
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError(_('Debe contener al menos un símbolo especial.'))


def validate_no_sql_injection(value):
    suspicious = ['--', ';', 'DROP', 'DELETE', 'UNION', 'SELECT']
    if any(s in str(value).upper() for s in suspicious):
        raise ValidationError(_('Entrada sospechosa detectada.'))