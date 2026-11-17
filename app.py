"""Lista de Mercado: sistema em FastAPI com banco SQLite (sqlite3, sem ORM).

Cada rota corresponde a um caso de uso da documentação do PDS I.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

PASTA = Path(__file__).parent
CAMINHO_BANCO = PASTA / "lista_de_mercado.db"  # RNF02: o banco é um único arquivo na pasta do projeto

app = FastAPI(title="Lista de Mercado")


# Modelos com os atributos e tipos do diagrama de classes (o Item não tem lista_id: ele só existe no banco).
class Lista(BaseModel):
    id: int
    nome: str


class Item(BaseModel):
    id: int
    nome: str
    quantidade: int
    preco: int  # preço unitário em centavos (D11, RNF04): 1250 = R$ 12,50
    comprado: bool


@contextmanager
def conectar():
    """Abre o banco, garante as tabelas do DER, grava as mudanças no fim e fecha."""
    conexao = sqlite3.connect(CAMINHO_BANCO)
    try:
        conexao.execute("CREATE TABLE IF NOT EXISTS Lista (id INTEGER PRIMARY KEY, nome TEXT)")
        conexao.execute(
            "CREATE TABLE IF NOT EXISTS Item (id INTEGER PRIMARY KEY, nome TEXT, quantidade INTEGER,"
            " preco INTEGER, comprado INTEGER, lista_id INTEGER REFERENCES Lista (id))"
        )
        yield conexao
        conexao.commit()
    finally:
        conexao.close()


def conferir_lista(conexao, lista_id):
    """Caminho ruim: lista inexistente devolve 404."""
    if conexao.execute("SELECT 1 FROM Lista WHERE id = ?", (lista_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Lista não encontrada.")


def conferir_item(conexao, item_id):
    """Caminho ruim: item inexistente devolve 404."""
    if conexao.execute("SELECT 1 FROM Item WHERE id = ?", (item_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Item não encontrado.")


@app.get("/")
def pagina():
    """RNF03: a única página do sistema, onde os 5 casos de uso são executados."""
    return FileResponse(PASTA / "index.html")


@app.post("/listas", status_code=201)
def criar_lista(nome: str = Body(embed=True)) -> Lista:
    """UC01 Criar lista: grava a lista no banco, que devolve o id gerado."""
    with conectar() as conexao:
        id_gerado = conexao.execute("INSERT INTO Lista (nome) VALUES (?) RETURNING id", (nome,)).fetchone()[0]
    return Lista(id=id_gerado, nome=nome)


@app.post("/listas/{lista_id}/itens", status_code=201)
def adicionar_item(lista_id: int, nome: str = Body(), quantidade: int = Body(), preco: int = Body()) -> Item:
    """UC02 Adicionar item: grava o item ligado à lista, com o preço em centavos, marcado como não comprado (0)."""
    with conectar() as conexao:
        conferir_lista(conexao, lista_id)
        id_gerado = conexao.execute(
            "INSERT INTO Item (nome, quantidade, preco, comprado, lista_id) VALUES (?, ?, ?, 0, ?) RETURNING id",
            (nome, quantidade, preco, lista_id),
        ).fetchone()[0]
    return Item(id=id_gerado, nome=nome, quantidade=quantidade, preco=preco, comprado=False)


@app.get("/listas")
def consultar_listas() -> list[Lista]:
    """UC03 Consultar lista (1ª rota): busca as listas cadastradas."""
    with conectar() as conexao:
        linhas = conexao.execute("SELECT id, nome FROM Lista ORDER BY id").fetchall()
    return [Lista(id=id_, nome=nome) for id_, nome in linhas]


@app.get("/listas/{lista_id}/itens")
def consultar_itens(lista_id: int) -> dict:
    """UC03 Consultar lista (2ª rota): busca os itens da lista escolhida e o total (RF08), calculado pelo banco."""
    with conectar() as conexao:
        conferir_lista(conexao, lista_id)
        linhas = conexao.execute(
            "SELECT id, nome, quantidade, preco, comprado FROM Item WHERE lista_id = ? ORDER BY id", (lista_id,)
        ).fetchall()
        # soma de preço × quantidade de todos os itens, comprados ou não; sem itens, a soma é nula e o COALESCE dá 0
        total = conexao.execute(
            "SELECT COALESCE(SUM(preco * quantidade), 0) FROM Item WHERE lista_id = ?", (lista_id,)
        ).fetchone()[0]
    # o banco guarda comprado como 0 ou 1; o modelo usa False ou True
    itens = [
        Item(id=id_, nome=nome, quantidade=qtd, preco=preco, comprado=bool(comprado))
        for id_, nome, qtd, preco, comprado in linhas
    ]
    return {"itens": itens, "total": total}


@app.put("/itens/{item_id}")
def alterar_item(
    item_id: int, nome: str = Body(), quantidade: int = Body(), preco: int = Body(), comprado: bool = Body()
) -> Item:
    """UC04 Alterar item: atualiza nome, quantidade, preço e situação de compra no banco."""
    with conectar() as conexao:
        conferir_item(conexao, item_id)
        conexao.execute(
            "UPDATE Item SET nome = ?, quantidade = ?, preco = ?, comprado = ? WHERE id = ?",
            (nome, quantidade, preco, int(comprado), item_id),
        )
    return Item(id=item_id, nome=nome, quantidade=quantidade, preco=preco, comprado=comprado)


@app.delete("/itens/{item_id}")
def excluir_item(item_id: int):
    """UC05 Excluir item: apaga o item do banco e confirma a exclusão."""
    with conectar() as conexao:
        conferir_item(conexao, item_id)
        conexao.execute("DELETE FROM Item WHERE id = ?", (item_id,))
    return {"mensagem": "Item excluído."}
