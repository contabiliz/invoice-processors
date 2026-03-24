import logging

from invoice_models.validators import (
    ValidationResult,
    validate_cnpj,
    validate_cpf_ou_cnpj,
    validate_data,
    validate_moeda_brl,
    validate_texto,
    validate_texto_numerico_44,
    validate_uf,
)

logger = logging.getLogger(__name__)

_VALIDATORS = {
    "cnpj": validate_cnpj,
    "cpf_ou_cnpj": validate_cpf_ou_cnpj,
    "texto_numerico_44": validate_texto_numerico_44,
    "moeda_brl": validate_moeda_brl,
    "data": validate_data,
    "uf": validate_uf,
    "texto": validate_texto,
}


class TypeValidator:
    def validate(self, value_type: str, raw_text: str) -> ValidationResult:
        validator = _VALIDATORS.get(value_type)
        if validator is None:
            logger.warning("Unknown value_type '%s', treating as texto.", value_type)
            validator = validate_texto

        return validator(raw_text)
