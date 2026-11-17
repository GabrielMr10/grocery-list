"""Testes da Lista de Mercado: UC01 a UC05 (com o preço do item, D11), total da lista (RF08, RNF04),
caminho ruim (404), RF07 e a página (RNF03).

Cada teste usa um arquivo .db temporário (pasta tmp_path do pytest), nunca o banco real.
"""
import importlib
import sqlite3

import pytest
from fastapi.testclient import TestClient

import app as sistema


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Aponta o sistema para um arquivo .db temporário e devolve o caminho dele."""
    arquivo = tmp_path / "teste.db"
    monkeypatch.setattr(sistema, "CAMINHO_BANCO", arquivo)
    return arquivo


@pytest.fixture
def cliente(banco):
    return TestClient(sistema.app)


def no_banco(arquivo, sql):
    """Lê direto do arquivo .db o que o sistema gravou."""
    conexao = sqlite3.connect(arquivo)
    try:
        return conexao.execute(sql).fetchall()
    finally:
        conexao.close()


def criar_lista_com_item(cliente):
    lista = cliente.post("/listas", json={"nome": "Feira"}).json()
    item = cliente.post(f"/listas/{lista['id']}/itens", json={"nome": "Banana", "quantidade": 6, "preco": 450}).json()
    return lista, item


# ---------------------------------------------------------------- caminho feliz

def test_uc01_criar_lista(cliente, banco):
    resposta = cliente.post("/listas", json={"nome": "Compras da semana"})
    assert resposta.status_code == 201
    assert resposta.json() == {"id": 1, "nome": "Compras da semana"}
    assert no_banco(banco, "SELECT id, nome FROM Lista") == [(1, "Compras da semana")]


def test_uc02_adicionar_item(cliente, banco):
    lista = cliente.post("/listas", json={"nome": "Feira"}).json()
    resposta = cliente.post(f"/listas/{lista['id']}/itens", json={"nome": "Banana", "quantidade": 6, "preco": 450})
    assert resposta.status_code == 201
    assert resposta.json() == {"id": 1, "nome": "Banana", "quantidade": 6, "preco": 450, "comprado": False}
    # gravado ligado à lista e como não comprado (0), como no DER
    assert no_banco(banco, "SELECT id, nome, quantidade, preco, comprado, lista_id FROM Item") == [(1, "Banana", 6, 450, 0, 1)]


def test_uc02_grava_o_preco_em_centavos(cliente, banco):
    lista = cliente.post("/listas", json={"nome": "Feira"}).json()
    cliente.post(f"/listas/{lista['id']}/itens", json={"nome": "Queijo", "quantidade": 1, "preco": 1250})
    # R$ 12,50 vira 1250 centavos, guardado como número inteiro (RNF04)
    assert no_banco(banco, "SELECT preco, typeof(preco) FROM Item") == [(1250, "integer")]


def test_uc03_consultar_lista(cliente):
    cliente.post("/listas", json={"nome": "Feira"})
    cliente.post("/listas", json={"nome": "Mercado"})
    cliente.post("/listas/1/itens", json={"nome": "Banana", "quantidade": 6, "preco": 450})
    cliente.post("/listas/2/itens", json={"nome": "Arroz", "quantidade": 1, "preco": 2599})
    assert cliente.get("/listas").json() == [{"id": 1, "nome": "Feira"}, {"id": 2, "nome": "Mercado"}]
    resposta = cliente.get("/listas/2/itens")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "itens": [{"id": 2, "nome": "Arroz", "quantidade": 1, "preco": 2599, "comprado": False}],
        "total": 2599,
    }


def test_uc04_alterar_item(cliente, banco):
    _, item = criar_lista_com_item(cliente)
    resposta = cliente.put(f"/itens/{item['id']}",
                           json={"nome": "Banana prata", "quantidade": 4, "preco": 520, "comprado": True})
    assert resposta.status_code == 200
    assert resposta.json() == {"id": 1, "nome": "Banana prata", "quantidade": 4, "preco": 520, "comprado": True}
    assert no_banco(banco, "SELECT nome, quantidade, preco, comprado FROM Item") == [("Banana prata", 4, 520, 1)]


def test_uc04_altera_o_preco(cliente, banco):
    _, item = criar_lista_com_item(cliente)
    # só o preço muda: de R$ 4,50 para R$ 3,99
    cliente.put(f"/itens/{item['id']}", json={"nome": "Banana", "quantidade": 6, "preco": 399, "comprado": False})
    assert no_banco(banco, "SELECT preco FROM Item") == [(399,)]


def test_uc05_excluir_item(cliente, banco):
    _, item = criar_lista_com_item(cliente)
    resposta = cliente.delete(f"/itens/{item['id']}")
    assert resposta.status_code == 200
    assert resposta.json() == {"mensagem": "Item excluído."}
    assert no_banco(banco, "SELECT * FROM Item") == []


# ---------------------------------------------------------------- total da lista (RF08, RNF04)

def test_rf08_total_e_a_soma_de_preco_vezes_quantidade(cliente):
    cliente.post("/listas", json={"nome": "Feira"})
    cliente.post("/listas", json={"nome": "Mercado"})
    cliente.post("/listas/1/itens", json={"nome": "Banana", "quantidade": 6, "preco": 450})
    cliente.post("/listas/1/itens", json={"nome": "Arroz", "quantidade": 2, "preco": 2599})
    cliente.post("/listas/2/itens", json={"nome": "Café", "quantidade": 1, "preco": 1890})  # outra lista: não entra
    # item comprado continua no total ("comprados ou não")
    cliente.put("/itens/2", json={"nome": "Arroz", "quantidade": 2, "preco": 2599, "comprado": True})
    # 6 × 450 + 2 × 2599 = 2700 + 5198 = 7898 centavos (R$ 78,98)
    assert cliente.get("/listas/1/itens").json()["total"] == 7898


def test_rnf04_dez_centavos_vezes_tres_da_trinta(cliente):
    cliente.post("/listas", json={"nome": "Feira"})
    cliente.post("/listas/1/itens", json={"nome": "Bala", "quantidade": 3, "preco": 10})
    total = cliente.get("/listas/1/itens").json()["total"]
    assert total == 30  # R$ 0,30 exato (em float, 0.10 * 3 daria 0.30000000000000004)
    assert type(total) is int


def test_rf08_lista_sem_itens_tem_total_zero(cliente):
    cliente.post("/listas", json={"nome": "Feira"})
    assert cliente.get("/listas/1/itens").json() == {"itens": [], "total": 0}


# ---------------------------------------------------------------- caminho ruim (404)

def test_uc02_lista_inexistente(cliente):
    resposta = cliente.post("/listas/99/itens", json={"nome": "Arroz", "quantidade": 1, "preco": 2599})
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Lista não encontrada."}


def test_uc03_lista_inexistente(cliente):
    resposta = cliente.get("/listas/99/itens")
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Lista não encontrada."}


def test_uc04_item_inexistente(cliente):
    resposta = cliente.put("/itens/99", json={"nome": "Arroz", "quantidade": 1, "preco": 2599, "comprado": True})
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Item não encontrado."}


def test_uc05_item_inexistente(cliente):
    resposta = cliente.delete("/itens/99")
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Item não encontrado."}


# ---------------------------------------------------------------- RF07 e RNF03

def test_rf07_dados_continuam_depois_de_reiniciar(banco, monkeypatch):
    with TestClient(sistema.app) as cliente:
        criar_lista_com_item(cliente)
    # "fecha e abre o sistema": recarrega o módulo e aponta de novo para o mesmo arquivo
    novo = importlib.reload(sistema)
    monkeypatch.setattr(novo, "CAMINHO_BANCO", banco)
    with TestClient(novo.app) as cliente:
        assert cliente.get("/listas").json() == [{"id": 1, "nome": "Feira"}]
        assert cliente.get("/listas/1/itens").json() == {
            "itens": [{"id": 1, "nome": "Banana", "quantidade": 6, "preco": 450, "comprado": False}],
            "total": 2700,
        }


def test_rnf03_pagina_unica(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/html")
