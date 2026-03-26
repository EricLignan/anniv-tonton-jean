"""
Ajouter un cadeau au site anniversaire en une commande.

Usage :
    python scripts/add_gift.py "Prenom" chemin/vers/fichier.ogg
    python scripts/add_gift.py "Prenom" chemin/vers/fichier.ogg --photo chemin/vers/photo.jpeg
    python scripts/add_gift.py "Prenom et Prenom" chemin/vers/video.mp4
    python scripts/add_gift.py --deploy          # git add + commit + push
    python scripts/add_gift.py --list            # afficher les cadeaux actuels

Le script :
1. Detecte le type (audio/video/image) par extension
2. Convertit .ogg/.aac/.webm en .mp3 via ffmpeg si necessaire
3. Copie dans assets/ avec nom normalise
4. Met a jour gifts.json
5. Affiche le resultat
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

# === CONFIGURATION ===
PROJECT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_DIR / "assets"
GIFTS_JSON = PROJECT_DIR / "gifts.json"

# ffmpeg : chercher dans le PATH d'abord, puis emplacement connu
FFMPEG_KNOWN = Path(
    r"C:\Users\eminy\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
)
FFMPEG = "ffmpeg" if shutil.which("ffmpeg") else str(FFMPEG_KNOWN)

AUDIO_EXTENSIONS = {".ogg", ".aac", ".webm", ".m4a", ".wav", ".flac", ".wma"}
AUDIO_DIRECT = {".mp3"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".png", ".gif", ".webp"}


def normalize_name(name: str) -> str:
    """Normalise un prenom pour en faire un nom de fichier."""
    # Retirer accents
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ASCII", "ignore").decode("ASCII")
    # Minuscules, espaces → tirets, retirer caracteres speciaux
    slug = re.sub(r"[^a-z0-9\-]", "", ascii_name.lower().replace(" ", "-"))
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "cadeau"


def detect_type(filepath: Path) -> str:
    """Detecte le type de media par extension."""
    ext = filepath.suffix.lower()
    if ext in AUDIO_EXTENSIONS or ext in AUDIO_DIRECT:
        return "audio"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    raise ValueError(f"Extension non supportee : {ext}")


def needs_conversion(filepath: Path) -> bool:
    """Verifie si le fichier audio doit etre converti en .mp3."""
    return filepath.suffix.lower() in AUDIO_EXTENSIONS


def convert_to_mp3(source: Path, target: Path) -> None:
    """Convertit un fichier audio en .mp3 via ffmpeg."""
    result = subprocess.run(
        [FFMPEG, "-y", "-i", str(source), "-codec:a", "libmp3lame", "-b:a", "128k", str(target)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg erreur : {result.stderr[-300:]}")


def load_gifts() -> list:
    """Charge gifts.json."""
    if GIFTS_JSON.exists():
        with open(GIFTS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_gifts(gifts: list) -> None:
    """Sauvegarde gifts.json."""
    with open(GIFTS_JSON, "w", encoding="utf-8") as f:
        json.dump(gifts, f, ensure_ascii=False, indent=4)


def next_id(gifts: list) -> int:
    """Retourne le prochain ID disponible."""
    if not gifts:
        return 1
    return max(g["id"] for g in gifts) + 1


def find_unique_filename(base_slug: str, ext: str) -> str:
    """Trouve un nom de fichier unique dans assets/."""
    candidate = f"{base_slug}{ext}"
    if not (ASSETS_DIR / candidate).exists():
        return candidate
    i = 2
    while (ASSETS_DIR / f"{base_slug}-{i}{ext}").exists():
        i += 1
    return f"{base_slug}-{i}{ext}"


def add_gift(name: str, media_path: Path, photo_path: Path | None = None) -> dict:
    """Ajoute un cadeau : convertit, copie, met a jour gifts.json."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    media_type = detect_type(media_path)
    slug = normalize_name(name)

    # Traiter le fichier media
    if media_type == "audio" and needs_conversion(media_path):
        target_name = find_unique_filename(slug, ".mp3")
        target = ASSETS_DIR / target_name
        print(f"  Conversion {media_path.name} -> {target_name} ...")
        convert_to_mp3(media_path, target)
    elif media_type == "audio":
        target_name = find_unique_filename(slug, ".mp3")
        target = ASSETS_DIR / target_name
        shutil.copy2(media_path, target)
    elif media_type == "video":
        ext = media_path.suffix.lower()
        target_name = find_unique_filename(slug, ext)
        target = ASSETS_DIR / target_name
        shutil.copy2(media_path, target)
    else:
        raise ValueError(f"Type '{media_type}' non supporte comme cadeau principal. Utiliser --photo pour les images.")

    size_kb = target.stat().st_size // 1024
    print(f"  OK {target_name} ({size_kb} Ko)")

    # Traiter la photo optionnelle
    image_rel = None
    if photo_path:
        if not photo_path.exists():
            print(f"  ATTENTION : photo introuvable : {photo_path}")
        else:
            photo_ext = photo_path.suffix.lower()
            photo_name = find_unique_filename(slug, photo_ext)
            shutil.copy2(photo_path, ASSETS_DIR / photo_name)
            image_rel = f"assets/{photo_name}"
            print(f"  OK photo : {photo_name}")

    # Mettre a jour gifts.json
    gifts = load_gifts()
    new_gift = {
        "id": next_id(gifts),
        "name": name,
        "type": media_type,
        "file": f"assets/{target_name}",
        "image": image_rel,
    }
    gifts.append(new_gift)
    save_gifts(gifts)

    print(f"\n  Cadeau #{new_gift['id']} ajoute : {name} ({media_type})")
    print(f"  Total : {len(gifts)} cadeaux")

    return new_gift


def deploy():
    """Git add + commit + push."""
    import os
    os.chdir(str(PROJECT_DIR))

    # Verifier qu'il y a des changements
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not status.stdout.strip():
        print("Rien a deployer (pas de changements).")
        return

    print("Changements detectes :")
    print(status.stdout)

    # Compter les nouveaux cadeaux depuis le dernier commit
    gifts = load_gifts()
    n = len(gifts)

    subprocess.run(["git", "add", "gifts.json", "assets/"], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"feat: ajout cadeaux (total: {n})"],
        check=True
    )
    subprocess.run(["git", "push"], check=True)
    print(f"\nDeploye ! Le site sera mis a jour dans ~1 minute.")


def list_gifts():
    """Affiche les cadeaux actuels."""
    gifts = load_gifts()
    if not gifts:
        print("Aucun cadeau dans gifts.json")
        return
    print(f"\n{len(gifts)} cadeaux :\n")
    for g in gifts:
        photo = " + photo" if g.get("image") else ""
        print(f"  #{g['id']:2d}  {g['name']:<30s}  {g['type']:<6s}  {g['file']}{photo}")


def main():
    parser = argparse.ArgumentParser(description="Ajouter un cadeau au site anniversaire")
    parser.add_argument("name", nargs="?", help="Prenom du contributeur")
    parser.add_argument("media", nargs="?", help="Chemin vers le fichier media (audio ou video)")
    parser.add_argument("--photo", help="Chemin vers une photo du contributeur (optionnel)")
    parser.add_argument("--deploy", action="store_true", help="Git add + commit + push")
    parser.add_argument("--list", action="store_true", help="Afficher les cadeaux actuels")

    args = parser.parse_args()

    if args.list:
        list_gifts()
        return

    if args.deploy:
        deploy()
        return

    if not args.name or not args.media:
        parser.error("Le prenom et le fichier media sont requis. Ex: python add_gift.py \"Prenom\" fichier.ogg")

    media_path = Path(args.media)
    if not media_path.exists():
        print(f"ERREUR : fichier introuvable : {media_path}")
        sys.exit(1)

    photo_path = Path(args.photo) if args.photo else None
    if photo_path and not photo_path.exists():
        print(f"ERREUR : photo introuvable : {photo_path}")
        sys.exit(1)

    add_gift(args.name, media_path, photo_path)


if __name__ == "__main__":
    main()
