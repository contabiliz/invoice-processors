import logging
from ..schemas import TypeValidationResult
from ..text.validators import (
    validate_cnpj,
    validate_cpf_ou_cnpj,
    validate_texto_numerico_44,
    validate_moeda_brl,
    validate_data,
    validate_cidade_uf,
    validate_texto,
)

logger = logging.getLogger(__name__)

_VALIDATORS = {
    "cnpj": validate_cnpj,
    "cpf_ou_cnpj": validate_cpf_ou_cnpj,
    "texto_numerico_44": validate_texto_numerico_44,
    "moeda_brl": validate_moeda_brl,
    "data": validate_data,
    "cidade_uf": validate_cidade_uf,
    "texto": validate_texto,
}


class TypeValidator:
    def validate(self, value_type: str, raw_text: str) -> TypeValidationResult:
        validator = _VALIDATORS.get(value_type)
        if validator is None:
            logger.warning("Unknown value_type '%s', treating as texto.", value_type)
            validator = validate_texto

        ok, normalized_value, reason = validator(raw_text)
        return TypeValidationResult(
            ok=ok, normalized_value=normalized_value, reason=reason
        )
