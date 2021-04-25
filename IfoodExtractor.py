import json
import requests
import csv
from datetime import date, datetime
import logging, coloredlogs
import re


class IfoodExtractor:
    def __init__(self):
        self.logger = logging.getLogger("ifood_extractor_app")
        self.logger.setLevel(logging.DEBUG)

        self.fh = logging.FileHandler("ifood_extractor_app.log")
        self.fh.setLevel(logging.ERROR)

        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.INFO)

        self.logger.addHandler(self.ch)

        coloredlogs.install(
            level="DEBUG",
            logger=self.logger,
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    # Tenta adquirir a key do iFood
    def get_key(self, email=None, phone=None):
        self.logger.info("Coletando chave de acesso...")
        # Se o telefone foi informado, o formato do payload difere do de e-mail
        if phone:
            payload = {
                "phone": {
                    "country_code": 55,
                    "area_code": phone[:2],
                    "number": phone[2:],
                },
                "tenant_id": "IFO",
                "type": "PHONE",
            }
        elif email:
            payload = {"email": email, "tenant_id": "IFO", "type": "EMAIL"}
        else:
            self.logger.error(
                "Chave de acesso não encontrada! Email ou celular inválido(s) ou algum problema no acesso ao iFood!"
            )
            raise NameError("ACCESS KEY NOT FOUND")

        # Realiza a request
        auth_codes_url = "https://marketplace.ifood.com.br/v1/identity-providers/OTP/authorization-codes"
        auth_codes_response = requests.post(auth_codes_url, json=payload)
        auth_codes_response_json = json.loads(auth_codes_response.content)

        # Se a key foi obtida, retorna ela, se não, retorna uma string vazia
        key = (
            auth_codes_response_json["key"] if "key" in auth_codes_response_json else ""
        )
        return key

    # Tenta adquirir os tokens de acesso a partir da key
    # Retorna um dict {'access_token': access_token, 'refresh_token': refresh_token, 'account_id': account_id}
    def get_access_tokens(self, code, key, email):
        self.logger.info("Coletando tokens de acesso...")
        # Com a key obtida, faz a requisição dos tokens de acesso
        access_tokens_url = (
            "https://marketplace.ifood.com.br/v1/identity-providers/OTP/access-tokens?"
        )
        params = {"key": key, "auth_code": code}
        access_tokens_response = requests.get(access_tokens_url, params=params)
        access_tokens_response_json = json.loads(access_tokens_response.content)

        # Se o iFood não retornou o token de acesso, retorna um dict com todas as chaves com strings vazias
        if "access_token" in access_tokens_response_json:
            access_token = access_tokens_response_json["access_token"]
        else:
            self.logger.error("Token de acesso não retornado pelo iFood.")
            raise NameError("ACCESS TOKEN NOT FOUND")

        # Realiza um POST para autenticar com o token de acesso e receber o refesh token e a account id
        # Etapa de autenticação
        payload = {
            "device_id": "1",
            "email": email,
            "tenant_id": "IFO",
            "token": access_token,
        }
        authentications_url = (
            "https://marketplace.ifood.com.br/v2/identity-providers/OTP/authentications"
        )
        authentications_response = requests.post(authentications_url, json=payload)
        authentications_response_json = json.loads(authentications_response.content)

        # Se o iFood não retornou todos os tokens e a account id, retorna um dict com todas as chaves com strings vazias
        if "account_id" in authentications_response_json:
            access_token = authentications_response_json["access_token"]
            refresh_token = authentications_response_json["refresh_token"]
            account_id = authentications_response_json["account_id"]
        else:
            self.logger.error("Token de acesso não retornado pelo iFood.")
            raise NameError("ACCESS TOKEN NOT FOUND")

        access_tokens_dict = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "account_id": account_id,
        }
        return access_tokens_dict

    # Consulta a lista de todos os pedidos realizados no iFood
    # Ele fica iterando as páginas até não receber mais pedidos na resposta (pages, orders_response)
    def get_all_orders(self, auth_data):
        self.logger.info("Coletando lista de pedidos...")
        access_token = auth_data["access_token"]
        account_id = auth_data["account_id"]

        # inclui access token no bearer
        orders_url = "https://marketplace.ifood.com.br/v4/customers/me/orders?"
        page = 0
        size = 25
        orders = []
        while True:
            params = {"page": page, "size": size}
            bearer_token = "Bearer " + str(access_token)
            headers = {"account_id": account_id, "authorization": bearer_token}

            orders_response = requests.get(orders_url, headers=headers, params=params)
            orders_response_json = json.loads(orders_response.content)

            if len(orders_response_json) == 0:
                break

            page += 1
            orders += orders_response_json

        self.logger.info(
            "Pedidos coletados com sucesso, foram encontrados {} pedidos em sua conta!".format(
                len(orders)
            )
        )
        return orders

    # Faz um tratamento dos dados da lista de orders para jogar em um arquivo csv
    def parse_to_csv(self, orders):
        list_of_orders = []
        for order in orders:
            parsed_order = {}
            parsed_order["id"] = order["id"]
            parsed_order["creation_date"] = order["createdAt"]
            parsed_order["status"] = order["lastStatus"]
            parsed_order["merchant"] = order["merchant"]["name"]
            parsed_order["pay_method"] = order["payments"]["methods"][0]["method"][
                "name"
            ]
            parsed_order["pay_type"] = order["payments"]["methods"][0]["type"]["name"]
            parsed_order["total"] = str(
                order["payments"]["total"]["value"] / 100.0
            ).replace(".", ",")
            parsed_order["items"] = (
                json.dumps(order["bag"]["items"][0], ensure_ascii=False)
                .encode("cp1252", errors="ignore")
                .decode("cp1252")
            )  # Encondig para tratar acentos, ignora emojis (perigoso, risco de perder dados)
            list_of_orders.append(parsed_order)
        return list_of_orders

    # Joga os valores em um arquivo csv
    def output_to_csv(self, orders):
        self.logger.info("Gerando csv...")
        list_of_orders = self.parse_to_csv(orders)

        # Se a lista veio vazia, retorna uma string vazia
        if not list_of_orders:
            self.logger.info(
                "Arquivo não foi gerado pois não foram encontrados pedidos em sua conta."
            )
            return

        keys = list_of_orders[0].keys()
        filename = datetime.today().strftime("%Y%m%dT%H%M%S") + "-orders.csv"
        with open(filename, "w", newline="", encoding="cp1252") as f:
            dict_writer = csv.DictWriter(
                f, keys, delimiter=";", quotechar="'"
            )  # TODO fix me, alguns restaurantes estão vindo com aspas simples em torno do nome
            dict_writer.writeheader()
            dict_writer.writerows(list_of_orders)

        self.logger.info("Arquivo {} gerado com sucesso!".format(filename))
