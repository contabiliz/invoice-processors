"""Pure validation and normalization functions for Brazilian fiscal field types."""

import re
from datetime import datetime

_UF_CODES = {
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
}


# -- CNPJ -------------------------------------------------------------------


def _cnpj_check_digit(digits: str, weights: list[int]) -> int:
    remainder = sum(int(d) * w for d, w in zip(digits, weights)) % 11
    return 0 if remainder < 2 else 11 - remainder


def validate_cnpj(raw: str) -> tuple[bool, str | None, str | None]:
    digits = re.sub(r"\D", "", raw)
    if len(digits) != 14:
        return False, None, f"CNPJ deve ter 14 dígitos, encontrado {len(digits)}"
    if len(set(digits)) == 1:
        return False, None, "CNPJ com todos os dígitos iguais é inválido"
    d1 = _cnpj_check_digit(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = _cnpj_check_digit(digits[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    if int(digits[12]) != d1 or int(digits[13]) != d2:
        return False, None, "Dígitos verificadores do CNPJ inválidos"
    normalized = (
        f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    )
    return True, normalized, None


# -- CPF --------------------------------------------------------------------


def _cpf_check_digit(digits: str, weights: list[int]) -> int:
    remainder = (sum(int(d) * w for d, w in zip(digits, weights)) * 10) % 11
    return 0 if remainder >= 10 else remainder


def validate_cpf(raw: str) -> tuple[bool, str | None, str | None]:
    digits = re.sub(r"\D", "", raw)
    if len(digits) != 11:
        return False, None, f"CPF deve ter 11 dígitos, encontrado {len(digits)}"
    if len(set(digits)) == 1:
        return False, None, "CPF com todos os dígitos iguais é inválido"
    d1 = _cpf_check_digit(digits[:9], list(range(10, 1, -1)))
    d2 = _cpf_check_digit(digits[:10], list(range(11, 1, -1)))
    if int(digits[9]) != d1 or int(digits[10]) != d2:
        return False, None, "Dígitos verificadores do CPF inválidos"
    normalized = re.sub(r"\D", "", digits)
    return True, normalized, None


# -- CPF ou CNPJ ------------------------------------------------------------


def validate_cpf_ou_cnpj(raw: str) -> tuple[bool, str | None, str | None]:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 14:
        return validate_cnpj(raw)
    if len(digits) == 11:
        return validate_cpf(raw)
    return False, None, f"CPF/CNPJ deve ter 11 ou 14 dígitos, encontrado {len(digits)}"


# -- Chave de acesso (44 dígitos) -------------------------------------------


def validate_texto_numerico_44(raw: str) -> tuple[bool, str | None, str | None]:
    digits = re.sub(r"\D", "", raw)
    if len(digits) != 44:
        return (
            False,
            None,
            f"Chave de acesso deve ter 44 dígitos, encontrado {len(digits)}",
        )
    return True, digits, None


# -- Moeda BRL --------------------------------------------------------------

_MOEDA_STRIP = re.compile(r"[R$\s]")
_MOEDA_CLEAN = re.compile(r"[^\d,.]")


def validate_moeda_brl(raw: str) -> tuple[bool, str | None, str | None]:
    cleaned = _MOEDA_STRIP.sub("", raw)
    cleaned = _MOEDA_CLEAN.sub("", cleaned)
    if not cleaned:
        return False, None, "Valor monetário vazio após limpeza"

    # Brazilian format: periods as thousands separator, comma as decimal
    if "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) != 2:
            return False, None, f"Formato monetário ambíguo: '{raw}'"
        integer_part = parts[0].replace(".", "")
        decimal_part = parts[1]
        normalized = f"{integer_part}.{decimal_part}"
    elif cleaned.count(".") == 1:
        # single dot — treat as decimal separator (e.g. "1234.56")
        normalized = cleaned
    else:
        # no separator — integer value
        normalized = cleaned.replace(".", "")

    try:
        float(normalized)
    except ValueError:
        return False, None, f"Não foi possível converter '{raw}' para valor numérico"

    return True, normalized, None


# -- Data -------------------------------------------------------------------

_DATE_FORMATS = [
    ("%d/%m/%Y", r"\d{2}/\d{2}/\d{4}"),
    ("%d-%m-%Y", r"\d{2}-\d{2}-\d{4}"),
    ("%Y-%m-%d", r"\d{4}-\d{2}-\d{2}"),
    ("%d/%m/%y", r"\d{2}/\d{2}/\d{2}"),
]


def validate_data(raw: str) -> tuple[bool, str | None, str | None]:
    cleaned = raw.strip()
    for fmt, pattern in _DATE_FORMATS:
        match = re.search(pattern, cleaned)
        if match:
            try:
                dt = datetime.strptime(match.group(), fmt)
                return True, dt.strftime("%Y-%m-%d"), None
            except ValueError:
                continue
    return False, None, f"Data não reconhecida: '{raw}'"


# -- Cidade/UF --------------------------------------------------------------

_CIDADE_UF_PATTERN = re.compile(
    r"^(.+?)[\s/\-]+(" + "|".join(_UF_CODES) + r")$",
    re.IGNORECASE,
)


def validate_cidade_uf(raw: str) -> tuple[bool, str | None, str | None]:
    cleaned = raw.strip()
    match = _CIDADE_UF_PATTERN.match(cleaned)
    if not match:
        return False, None, f"Formato cidade/UF não reconhecido: '{raw}'"
    cidade = match.group(1).strip()
    uf = match.group(2).upper()
    return True, f"{cidade}/{uf}", None


# -- Texto ------------------------------------------------------------------


def validate_texto(raw: str) -> tuple[bool, str | None, str | None]:
    normalized = " ".join(raw.split())
    if not normalized:
        return False, None, "Texto vazio"
    return True, normalized, None
