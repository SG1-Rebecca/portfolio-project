import secrets
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings


def generate_otp(user) -> str:
    otp = f"{secrets.randbelow(1_000_000):06d}"
    cache.set(f"otp:{user.pk}", otp, timeout=300)
    return otp


def verify_otp(user, otp: str) -> bool:
    # Retrieve the stored OTP from the cache.
    cached = cache.get(f"otp:{user.pk}")
    if cached is None:
        return False

    # Validate the OTP and remove it after successful verification.
    if secrets.compare_digest(cached, otp):
        cache.delete(f"otp:{user.pk}")
        return True
    return False


def send_otp_email(user, otp: str):
    send_mail(
        subject="Your OTP code",
        message=f"Your code is: {otp} (valid 5 minutes)",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
