from django.core.exceptions import ValidationError


def _clean_rut(value: str) -> tuple[str, str]:
    
    #Normaliza un RUT: quita puntos y guion, y separa cuerpo y DV.
    #Retorna (cuerpo, dv) en mayúsculas.
    if value is None:
        raise ValidationError("RUT requerido")

    s = str(value).strip().upper().replace(".", "").replace("-", "")
    if len(s) < 2:
        raise ValidationError("RUT incompleto")

    cuerpo, dv = s[:-1], s[-1]
    if not cuerpo.isdigit():
        raise ValidationError("El RUT debe contener solo dígitos antes del dígito verificador")
    return cuerpo, dv


def _dv_mod11(cuerpo: str) -> str:

    #Calcula el dígito verificador para un cuerpo de RUT usando módulo 11.
    total = 0
    factor = 2
    for d in reversed(cuerpo):
        total += int(d) * factor
        factor = 2 if factor == 7 else factor + 1

    resto = total % 11
    if resto == 0:
        return "0"
    if resto == 1:
        return "K"
    return str(11 - resto)


def validate_rut_chileno(value: str) -> None:
    
    #Valida un RUT chileno (con o sin puntos/guion) mediante módulo 11.

    #Acepta formatos como: `12345678-5`, `12.345.678-5`, `123456785`.
    #Lanza `ValidationError` si es inválido.
    
    cuerpo, dv = _clean_rut(value)
    dv_calc = _dv_mod11(cuerpo)
    if dv != dv_calc:
        raise ValidationError("RUT inválido: dígito verificador no coincide")


def normalizar_rut(value: str) -> str:

    #Devuelve el RUT en formato `cuerpo-dv` sin puntos (por ejemplo, `12345678-5`).
    cuerpo, dv = _clean_rut(value)
    return f"{int(cuerpo)}-{dv}"


def formatear_rut(value: str) -> str:

    #Devuelve el RUT formateado con puntos y guion (por ejemplo, `12.345.678-5`).
    cuerpo, dv = _clean_rut(value)
    cuerpo_formateado = f"{int(cuerpo):,}".replace(",", ".")
    return f"{cuerpo_formateado}-{dv}"
