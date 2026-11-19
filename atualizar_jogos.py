"""Gera jogos.json a partir dos jogos (SWF e HTML) organizados por categoria.

Entradas que ja existem no jogos.json sao preservadas:
- jogos de outros formatos (ex.: ROMs .zip do MAME/Neo Geo) continuam no catalogo
  enquanto o arquivo existir;
- nome e plataforma editados a mao nao sao sobrescritos.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

# Extensao encontrada na pasta -> plataforma usada pelo index.html.
PLATAFORMAS = {
    ".swf": "flash",
    ".html": "html",
    ".htm": "html",
}


def nome_do_jogo(caminho: Path) -> str:
    """Converte o nome do arquivo em um nome legivel para a interface."""
    nome = re.sub(r"[_-]+", " ", caminho.stem)
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome[:1].upper() + nome[1:] if nome else caminho.stem


def encontrar_jogos(pasta_jogos: Path) -> list[dict[str, str]]:
    """Monta os registros usando a pasta pai de cada jogo como categoria."""
    registros = []

    for arquivo in sorted(pasta_jogos.rglob("*"), key=lambda item: str(item).casefold()):
        plataforma = PLATAFORMAS.get(arquivo.suffix.casefold())
        if not arquivo.is_file() or plataforma is None:
            continue

        categoria = arquivo.parent.relative_to(pasta_jogos).parts
        if not categoria:
            continue

        # Em subpastas (jogos/<categoria>/<jogo>/), so o arquivo com o nome da
        # pasta ou um index.html e o jogo; o resto sao arquivos auxiliares.
        if len(categoria) > 1 and arquivo.stem.casefold() not in (
            arquivo.parent.name.casefold(),
            "index",
        ):
            continue

        registros.append(
            {
                "nome": nome_do_jogo(arquivo),
                "arquivo": arquivo.relative_to(pasta_jogos.parent).as_posix(),
                "categoria": categoria[0],
                "plataforma": plataforma,
            }
        )

    return registros


def carregar_catalogo(arquivo_json: Path) -> list[dict[str, str]]:
    """Le o jogos.json atual; retorna lista vazia se nao existir ou estiver invalido."""
    if not arquivo_json.exists():
        return []

    try:
        dados = json.loads(arquivo_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        print(f"Aviso: jogos.json invalido ({erro}); sera recriado do zero.")
        return []

    return [item for item in dados if isinstance(item, dict) and item.get("arquivo")]


def mesclar(
    encontrados: list[dict[str, str]],
    existentes: list[dict[str, str]],
    pasta_projeto: Path,
) -> list[dict[str, str]]:
    """Junta os jogos encontrados com o catalogo atual sem perder edicoes manuais."""
    por_arquivo = {item["arquivo"].casefold(): item for item in existentes}
    registros = []
    vistos = set()

    for novo in encontrados:
        chave = novo["arquivo"].casefold()
        vistos.add(chave)
        antigo = por_arquivo.get(chave)

        if antigo:
            # Mantem nome/plataforma/campos extras do catalogo;
            # categoria e caminho seguem a pasta real.
            registro = {**novo, **antigo}
            registro["arquivo"] = novo["arquivo"]
            registro["categoria"] = novo["categoria"]
        else:
            registro = novo

        registros.append(registro)

    # Jogos de outros formatos (MAME, Neo Geo, SNES...) que o scan nao cobre.
    for antigo in existentes:
        chave = antigo["arquivo"].casefold()
        if chave in vistos:
            continue
        vistos.add(chave)

        if (pasta_projeto / antigo["arquivo"]).is_file():
            registros.append(antigo)
        else:
            print(f"Removido (arquivo nao encontrado): {antigo['arquivo']}")

    return sorted(
        registros,
        key=lambda registro: (
            str(registro.get("categoria", "")).casefold(),
            str(registro.get("nome", "")).casefold(),
            registro["arquivo"].casefold(),
        ),
    )


def atualizar_catalogo(pasta_projeto: Path, fazer_backup: bool = True) -> int:
    pasta_jogos = pasta_projeto / "jogos"
    arquivo_json = pasta_projeto / "jogos.json"

    if not pasta_jogos.is_dir():
        raise FileNotFoundError(f"Pasta de jogos nao encontrada: {pasta_jogos}")

    existentes = carregar_catalogo(arquivo_json)
    registros = mesclar(encontrar_jogos(pasta_jogos), existentes, pasta_projeto)

    if fazer_backup and arquivo_json.exists():
        shutil.copy2(arquivo_json, arquivo_json.with_suffix(".json.bak"))

    arquivo_json.write_text(
        json.dumps(registros, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    return len(registros)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Atualiza jogos.json encontrando arquivos .swf e .html em jogos/<categoria>, "
            "preservando as demais entradas do catalogo."
        )
    )
    parser.add_argument(
        "--pasta",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Pasta do projeto; por padrao, a pasta deste script.",
    )
    parser.add_argument(
        "--sem-backup",
        action="store_true",
        help="Nao cria jogos.json.bak antes de atualizar o catalogo.",
    )
    args = parser.parse_args()

    quantidade = atualizar_catalogo(args.pasta.resolve(), fazer_backup=not args.sem_backup)
    print(f"Catalogo atualizado: {quantidade} jogos encontrados.")
    if not args.sem_backup:
        print("Backup criado em jogos.json.bak.")


if __name__ == "__main__":
    main()
