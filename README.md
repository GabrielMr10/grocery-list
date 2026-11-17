# Lista de Mercado

Sistema projetado na disciplina Projeto de Desenvolvimento de Software I e implementado em Projeto de Desenvolvimento de Software II, no curso de Engenharia de Software do Centro Universitário Filadélfia (UniFil).

**Autor:** Gabriel Mendonça de Meira (trabalho individual).

## O que o sistema faz

Organiza as compras de mercado de uma pessoa: criar listas, adicionar itens com nome e quantidade, consultar os itens de cada lista, alterar um item (inclusive marcar como comprado) e excluir itens. Tudo é feito por uma única página web. Os dados ficam no arquivo SQLite `lista_de_mercado.db`, criado na pasta do projeto na primeira vez que o sistema roda.

## Tecnologias

Python 3.13, FastAPI e SQLite, pelo módulo `sqlite3` da biblioteca padrão (sem ORM).

## Rotas

| Caso de uso | Método e caminho |
|---|---|
| UC01 Criar lista | `POST /listas` |
| UC02 Adicionar item | `POST /listas/{lista_id}/itens` |
| UC03 Consultar lista | `GET /listas` e `GET /listas/{lista_id}/itens` |
| UC04 Alterar item | `PUT /itens/{item_id}` |
| UC05 Excluir item | `DELETE /itens/{item_id}` |
| Página (RNF03) | `GET /` |

## Como instalar

Requer Python 3.13. Na pasta do projeto:

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

No Linux ou macOS, troque `.venv\Scripts\python` por `.venv/bin/python` neste e nos próximos comandos.

## Como rodar

```
.venv\Scripts\python -m uvicorn app:app
```

Abra http://127.0.0.1:8000 no navegador. Para parar, use Ctrl+C.

## Como testar

```
.venv\Scripts\python -m pytest
```

Os testes usam um banco temporário: o arquivo `lista_de_mercado.db` não é criado nem alterado por eles.
