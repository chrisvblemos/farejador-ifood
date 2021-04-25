![](https://i.imgur.com/mk1mR6K.png)

# Farejador do iFood

Código para extração de todo o histórico de pedidos realizados no iFood. O resultado é um arquivo csv com os dados de todos os pedidos. Útil para ser utilizado com o Data Studio ou Excel para analisar os gastos com comida durante o mês.

# iFood Extractor CLI

Para executar a extração de dados do iFood, execute o comando

`python ifood_extractor.py --email EMAIL`

Substituindo EMAIL pelo seu e-mail de login no iFood.

Caso deseje realizar a autenticação utilizando o seu celular, utilize o comando (note que é necessário informar o e-mail mesmo assim):

`python ifood_extractor.py --email EMAIL --phone CELULAR`

Em seguida, você deverá informar o código de autenticação que receberá via e-mail ou SMS. Essa etapa é necessário pois o iFood utiliza autenticação de 2 fatores.

O programa então executará a coleta e produzirá um arquivo csv com todos os pedidos que já realizou no iFood. A estrutura do CSV está explicitada a seguir.

# Estrutura do CSV

|Coluna             | Descrição                                                             |
| ----------------- | --------------------------------------------------------------------- |
|id                 | Contém o identificador do pedido realizado. Pode ser utilizado para acessar a URL com os detalhes do pedido (precisa estar logado) |
|creation_date      | Data de criação do pedido na plataforma iFood. |
|status             | Status final do pedido. |
|merchant           | Nome do vendedor (i.e. restaurante, mercado, etc) |
|pay_method         | Método de pagamento (DEBIT, CREDIT, MEAL_VOUCHER, IFOOD_WALLET) |
|pay_type           | Tipo de pagament (ONLINE, OFFLINE), i.e., online ou na entrega. |
|total              | Valor total do pedido, em reais. |
|items              | Descrição detalhada dos itens e valores. É um array de objetos em string JSON. |
