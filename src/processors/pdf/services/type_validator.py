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

from ..enums import ValueType

_VALIDATORS = {
    ValueType.CNPJ: validate_cnpj,
    ValueType.CPF_OU_CNPJ: validate_cpf_ou_cnpj,
    ValueType.TEXTO_NUMERICO_44: validate_texto_numerico_44,
    ValueType.MOEDA_BRL: validate_moeda_brl,
    ValueType.DATA: validate_data,
    ValueType.UF: validate_uf,
    ValueType.TEXTO: validate_texto,
}


class TypeValidator:
    def validate(self, value_type: ValueType, raw_text: str) -> ValidationResult:
        return _VALIDATORS[value_type](raw_text)
