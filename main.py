import argparse
import re

from IfoodExtractor import IfoodExtractor

EMAIL_REGEX = r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
CODE_REGEX = r"(^\d{5}$)"
CELPHONE_REGEX = r"(^\d{11}$)"

if __name__ == "__main__":
    ifood_extractor = IfoodExtractor()

    parser = argparse.ArgumentParser(
        description="Extrai histórico de pedidos realizados no iFood."
    )
    parser.add_argument(
        "--email",
        dest="email",
        required=True,
        type=str,
        default=None,
        help="[obrigatório] EMAIL de login no iFood",
    )
    parser.add_argument(
        "--phone",
        dest="phone",
        type=str,
        default=None,
        help="[opcional] CELULAR para login no iFood",
    )

    args = parser.parse_args()

    key = ifood_extractor.get_key(args.email, args.phone)

    code = ""
    while not re.match(CODE_REGEX, code, re.MULTILINE):
        code = str(
            input(
                "Informe o código de autorização que recebeu por e-mail ou SMS (5 digitos):\n"
            )
        )

    auth_data = ifood_extractor.get_access_tokens(code, key, args.email)
    orders = ifood_extractor.get_all_orders(auth_data)
    ifood_extractor.output_to_csv(orders)