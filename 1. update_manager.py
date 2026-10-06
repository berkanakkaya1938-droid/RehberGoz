import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


# ============================================================
# REHBER GÖZ UPDATE MANAGER - PROTOTYPE
# ============================================================

GITHUB_OWNER = "berkanakkaya1938-droid"
GITHUB_REPO = "rehber-goz"

BASE_DIR = Path("/opt/rehber-goz")

VERSIONS_DIR = BASE_DIR / "versions"
CURRENT_LINK = BASE_DIR / "current"

VERSION_FILE = BASE_DIR / "version.json"

API_URL = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)

ASSET_PREFIX = "rehber-goz-"


def get_current_version():
    """Cihazda çalışan mevcut sürümü oku."""

    if not VERSION_FILE.exists():
        return "0.0.0"

    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("version", "0.0.0")

    except Exception as e:
        print(f"❌ Versiyon okunamadı: {e}")
        return "0.0.0"


def get_latest_release():
    """GitHub'daki en son yayınlanmış Release bilgisini al."""

    print("☁️ GitHub'daki son release kontrol ediliyor...")

    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Rehber-Goz-Update-Manager"
        }
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data


def version_tuple(version):
    """0.2.1 -> (0, 2, 1)"""

    version = version.lstrip("v")

    return tuple(
        int(x)
        for x in version.split(".")
    )


def is_newer(current, latest):
    """Latest sürüm gerçekten daha yeni mi?"""

    try:
        return version_tuple(latest) > version_tuple(current)

    except ValueError:
        print("⚠️ Sürüm formatı anlaşılmadı.")
        return False


def find_release_asset(release):
    """Release içindeki uygulama ZIP dosyasını bul."""

    assets = release.get("assets", [])

    for asset in assets:

        name = asset.get("name", "")

        if (
            name.startswith(ASSET_PREFIX)
            and name.endswith(".zip")
        ):
            return asset

    return None


def download_file(url, destination):
    """Dosyayı güvenli şekilde indir."""

    print(f"⬇️ İndiriliyor: {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Rehber-Goz-Update-Manager"
        }
    )

    with urllib.request.urlopen(request, timeout=120) as response:

        with open(destination, "wb") as f:

            shutil.copyfileobj(
                response,
                f
            )


def calculate_sha256(path):
    """Dosyanın SHA-256 hash değerini hesapla."""

    sha256 = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def verify_checksum(file_path, expected_digest):
    """GitHub digest ile indirilen dosyayı karşılaştır."""

    if not expected_digest:
        print("⚠️ Release asset SHA-256 digest içermiyor.")
        return False

    if not expected_digest.startswith("sha256:"):
        print("❌ Desteklenmeyen digest formatı.")
        return False

    expected = expected_digest.split(":", 1)[1]

    actual = calculate_sha256(file_path)

    print(f"Beklenen SHA-256: {expected}")
    print(f"Hesaplanan SHA-256: {actual}")

    if actual != expected:

        print("❌ SHA-256 doğrulaması başarısız!")

        return False

    print("✅ SHA-256 doğrulaması başarılı.")

    return True


def install_version(zip_path, version):
    """Yeni sürümü eski sürüme dokunmadan kur."""

    target_dir = VERSIONS_DIR / version

    if target_dir.exists():
        print(f"⚠️ {version} zaten mevcut.")

        return target_dir

    temporary_dir = VERSIONS_DIR / f".{version}.installing"

    if temporary_dir.exists():
        shutil.rmtree(temporary_dir)

    temporary_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        f"📦 Yeni sürüm hazırlanıyor: {version}"
    )

    with zipfile.ZipFile(zip_path, "r") as z:

        z.extractall(temporary_dir)

    # ZIP'in içinde tek bir üst klasör varsa
    # içeriğini doğrudan version klasörüne taşı.
    entries = list(temporary_dir.iterdir())

    if len(entries) == 1 and entries[0].is_dir():

        source_dir = entries[0]

        for item in source_dir.iterdir():

            shutil.move(
                str(item),
                str(temporary_dir / item.name)
            )

        source_dir.rmdir()

    temporary_dir.rename(target_dir)

    print(
        f"✅ {version} kurulumu tamamlandı."
    )

    return target_dir


def health_check(version_dir):
    """Yeni sürüm için temel sağlık kontrolü."""

    print("🔎 Yeni sürüm kontrol ediliyor...")

    required_files = [
        "version.json"
    ]

    for filename in required_files:

        path = version_dir / filename

        if not path.exists():

            print(
                f"❌ Gerekli dosya bulunamadı: {filename}"
            )

            return False

    print("✅ Temel sağlık kontrolü başarılı.")

    return True


def activate_version(version):
    """
    current bağlantısını yeni sürüme geçir.

    Eski sürüm silinmez.
    """

    target = VERSIONS_DIR / version

    if not target.exists():

        print(
            "❌ Aktivasyon başarısız: "
            "hedef sürüm bulunamadı."
        )

        return False

    temporary_link = BASE_DIR / "current.new"

    if temporary_link.exists() or temporary_link.is_symlink():

        temporary_link.unlink()

    temporary_link.symlink_to(target)

    temporary_link.replace(CURRENT_LINK)

    print(
        f"✅ Aktif sürüm artık: {version}"
    )

    return True


def update():
    """Ana güncelleme işlemi."""

    current_version = get_current_version()

    print(
        f"📌 Mevcut sürüm: {current_version}"
    )

    release = get_latest_release()

    latest_version = release.get(
        "tag_name",
        ""
    )

    print(
        f"☁️ GitHub sürümü: {latest_version}"
    )

    if not is_newer(
        current_version,
        latest_version
    ):

        print("✅ Güncelleme gerekmiyor.")

        return

    print(
        f"🚀 Yeni sürüm bulundu: {latest_version}"
    )

    asset = find_release_asset(release)

    if not asset:

        print(
            "❌ Release içerisinde "
            "uygulama ZIP dosyası bulunamadı."
        )

        return

    asset_name = asset["name"]

    expected_digest = asset.get("digest")

    print(
        f"📦 Asset: {asset_name}"
    )

    with tempfile.TemporaryDirectory() as temp:

        zip_path = (
            Path(temp)
            / asset_name
        )

        download_file(
            asset["browser_download_url"],
            zip_path
        )

        if not verify_checksum(
            zip_path,
            expected_digest
        ):

            print(
                "❌ Güncelleme iptal edildi."
            )

            return

        version = latest_version.lstrip("v")

        new_version_dir = install_version(
            zip_path,
            version
        )

        if not health_check(
            new_version_dir
        ):

            print(
                "❌ Yeni sürüm sağlık kontrolünü "
                "geçemedi."
            )

            shutil.rmtree(
                new_version_dir,
                ignore_errors=True
            )

            return

        if not activate_version(
            version
        ):

            print(
                "❌ Yeni sürüm aktive edilemedi."
            )

            return

    print()
    print("🎉 Güncelleme tamamlandı!")
    print(
        "ℹ️ Servis yeniden başlatma "
        "bir sonraki aşamada eklenecek."
    )


if __name__ == "__main__":

    try:
        update()

    except Exception as e:

        print()
        print(
            f"❌ Güncelleme sırasında hata: {e}"
        )
