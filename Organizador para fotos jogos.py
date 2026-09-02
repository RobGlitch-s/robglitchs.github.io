from pathlib import Path

root = Path(r"c:\Users\906277\Documents\projeto 1")
img_dir = root / "imagens para colocar"

# Cria um mapa com nome do SWF -> caminho do arquivo
swf_by_stem = {
    p.stem.lower(): p
    for p in root.rglob("*.swf")
    if p.is_file()
}

moved = 0
skipped = 0
missing = []

for img in sorted(img_dir.iterdir()):
    if not img.is_file():
        continue

    if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        continue

    target_swf = swf_by_stem.get(img.stem.lower())

    if target_swf is None:
        missing.append(img.name)
        skipped += 1
        continue

    final_path = target_swf.with_suffix(img.suffix.lower())

    # Se já existe imagem no destino, não sobrescreve
    if final_path.exists() and final_path.resolve() != img.resolve():
        img.unlink()
        skipped += 1
        continue

    img.replace(final_path)
    moved += 1

print(f"moved={moved}")
print(f"skipped={skipped}")
print(f"missing={len(missing)}")
if missing:
    print("Arquivos sem match:", missing)