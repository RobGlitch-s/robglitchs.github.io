"""Gera jogos.json a partir dos arquivos SWF organizados por categoria."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


def nome_do_jogo(caminho: Path) -> str:
    """Converte o nome do arquivo em um nome legivel para a interface."""
    nome = re.sub(r"[_-]+", " ", caminho.stem)
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome[:1].upper() + nome[1:] if nome else caminho.stem


def encontrar_jogos(pasta_jogos: Path) -> list[dict[str, str]]:
    """Monta os registros usando a pasta pai de cada SWF como categoria."""
    registros = []

    for arquivo in sorted(pasta_jogos.rglob("*"), key=lambda item: str(item).casefold()):
        if not arquivo.is_file() or arquivo.suffix.casefold() != ".swf":
            continue

        categoria = arquivo.parent.relative_to(pasta_jogos).parts
        if not categoria:
            continue

        registros.append(
            {
                "nome": nome_do_jogo(arquivo),
                "arquivo": arquivo.relative_to(pasta_jogos.parent).as_posix(),
                "categoria": categoria[0],
            }
        )

    return sorted(
        registros,
        key=lambda registro: (
            registro["categoria"].casefold(),
            registro["nome"].casefold(),
            registro["arquivo"].casefold(),
        ),
    )


def atualizar_catalogo(pasta_projeto: Path, fazer_backup: bool = True) -> int:
    pasta_jogos = pasta_projeto / "jogos"
    arquivo_json = pasta_projeto / "jogos.json"

    if not pasta_jogos.is_dir():
        raise FileNotFoundError(f"Pasta de jogos nao encontrada: {pasta_jogos}")

    registros = encontrar_jogos(pasta_jogos)

    if fazer_backup and arquivo_json.exists():
        shutil.copy2(arquivo_json, arquivo_json.with_suffix(".json.bak"))

    arquivo_json.write_text(
        json.dumps(registros, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    return len(registros)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Atualiza jogos.json encontrando arquivos .swf em jogos/<categoria>."
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