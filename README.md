# Lista de Mercado

Sistema projetado na disciplina Projeto de Desenvolvimento de Software I e implementado em Projeto de Desenvolvimento de Software II, no curso de Engenharia de Software do Centro Universitário Filadélfia (UniFil).

**Autor:** Gabriel Mendonça de Meira (trabalho individual).

## O que o sistema faz

Organiza as compras de mercado de uma pessoa: criar listas, adicionar itens com nome, quantidade e preço, consultar os itens de cada lista com o total da lista, alterar um item (inclusive o preço e marcar como comprado) e excluir itens. O total é a soma de preço × quantidade de todos os itens da lista, comprados ou não, e é atualizado depois de cada inclusão, alteração ou exclusão.

Tudo é feito por uma única página web, que também funciona no celular (com 360 px de largura, sem rolagem horizontal). Na página, o preço é digitado e mostrado em reais (aceita vírgula ou ponto: `12,50` ou `12.50`); o sistema e o banco guardam o preço em centavos, como número inteiro (1250 = R$ 12,50), para o total não ter erro de arredondamento.

Os dados ficam no arquivo SQLite `lista_de_mercado.db`, criado na pasta do projeto na primeira vez que o sistema roda. Se você tiver um `lista_de_mercado.db` de uma versão sem preço, apague o arquivo antes de rodar: a tabela de itens ganhou a coluna `preco`.

## Tecnologias

Python 3.13, FastAPI e SQLite, pelo módulo `sqlite3` da biblioteca padrão (sem ORM).

## Rotas

| Caso de uso | Método e caminho |
|---|---|
| UC01 Criar lista | `POST /listas` |
| UC02 Adicionar item | `POST /listas/{lista_id}/itens` |
| UC03 Consultar lista | `GET /listas` e `GET /listas/{lista_id}/itens` (devolve os itens e o total) |
| UC04 Alterar item | `PUT /itens/{item_id}` |
| UC05 Excluir item | `DELETE /itens/{item_id}` |
| Página (RNF03) | `GET /` |

## Como instalar

Requer Python 3.13. Na pasta do projeto:

Windows:

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Linux e macOS:

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Como rodar

Windows:

```
.venv\Scripts\python -m uvicorn app:app
```

Linux e macOS:

```
.venv/bin/python -m uvicorn app:app
```

Abra http://127.0.0.1:8000 no navegador. Para parar, use Ctrl+C.

## Como testar

Windows:

```
.venv\Scripts\python -m pytest
```

Linux e macOS:

```
.venv/bin/python -m pytest
```

Os testes usam um banco temporário: o arquivo `lista_de_mercado.db` não é criado nem alterado por eles.
