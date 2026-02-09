"""
Utilitários de data/hora com fuso horário de Brasília (BRT - UTC-3).
"""

from datetime import datetime, timezone, timedelta

# Fuso horário de Brasília (UTC-3)
BRASILIA_OFFSET = timedelta(hours=-3)
BRASILIA_TZ = timezone(BRASILIA_OFFSET, name="BRT")


def now_brasilia() -> datetime:
    """Retorna a data/hora atual no fuso horário de Brasília."""
    return datetime.now(BRASILIA_TZ)


def now_utc() -> datetime:
    """Retorna a data/hora atual em UTC."""
    return datetime.now(timezone.utc)


def to_brasilia(dt: datetime) -> datetime:
    """
    Converte uma datetime para o fuso horário de Brasília.
    Se a datetime não tiver timezone, assume que é UTC.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Assume UTC se não tiver timezone
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(BRASILIA_TZ)


def to_utc(dt: datetime) -> datetime:
    """
    Converte uma datetime para UTC.
    Se a datetime não tiver timezone, assume que é Brasília.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Assume Brasília se não tiver timezone
        dt = dt.replace(tzinfo=BRASILIA_TZ)

    return dt.astimezone(timezone.utc)


def format_brasilia(dt: datetime, fmt: str = "%d/%m/%Y %H:%M") -> str:
    """Formata uma datetime no padrão brasileiro."""
    if dt is None:
        return "-"

    brasilia_dt = to_brasilia(dt)
    return brasilia_dt.strftime(fmt)


def parse_iso_to_brasilia(iso_string: str) -> datetime:
    """
    Parse uma string ISO 8601 e retorna datetime no fuso de Brasília.
    """
    if not iso_string:
        return None

    try:
        # Tenta parse ISO com timezone
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    except ValueError:
        # Fallback para formato sem timezone
        dt = datetime.fromisoformat(iso_string)
        dt = dt.replace(tzinfo=timezone.utc)

    return to_brasilia(dt)
