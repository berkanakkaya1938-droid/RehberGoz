import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# AYARLAR
# ============================================================

load_dotenv()

GITHUB_OWNER = "berkanakkaya1938-droid"
GITHUB_REPO = "RehberGoz"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

BASE_DIR = Path("/opt/rehber-goz")
VERSIONS_DIR = BASE_DIR / "versions"
CURRENT_LINK = BASE_DIR / "current"

API_URL = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)

ASSET_PREFIX = "rehber-goz-"


# ============================================================
# GITHUB HEADER
# ============================================================

def github_headers(accept="application/vnd.github+json"):
    if not GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN bulunamadı. "
            ".env dosyasını kontrol edin."
        )

    return {
        "Accept": accept,
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Rehber-Goz-Update-Manager",
    }


# ============================================================
# MEVCUT SÜRÜMÜ OKU
# ============================================================

def get_current_version():

    version_file = CURRENT_LINK / "version.json"

    if not version_file.exists():
        return "0.0.0"

    try:
        with open(version_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("version", "0.0.0")

    except Exception as e:
        print(f"❌ Mevcut sürüm okunamadı: {e}")
        return "0.0.0"


# ============================================================
# GITHUB'DAN SON RELEASE'İ AL
# ============================================================

def get_latest_release():

    print("☁️ GitHub'daki son release kontrol ediliyor...")

    request = urllib.request.Request(
        API_URL,
        headers=github_headers(),
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(
            response.read().decode("utf-8")
        )

    return data


# ============================================================
# SÜRÜM KARŞILAŞTIRMA
# ============================================================

def version_tuple(version):

    version = version.lstrip("v")

    return tuple(
        int(x)
        for x in version.split(".")
    )


def is_newer(current, latest):

    try:
        return version_tuple(latest) > version_tuple(current)

    except ValueError:
        print("⚠️ Sürüm formatı anlaşılmadı.")
        return False


# ============================================================
# RELEASE ASSET BUL
# ============================================================

def find_release_asset(release):

    assets = release.get("assets", [])

    for asset in assets:

        name = asset.get("name", "")

        if (
            name.startswith(ASSET_PREFIX)
            and name.endswith(".zip")
        ):
            return asset

    return None


# ============================================================
# DOSYA İNDİR
# ============================================================

def download_file(url, destination):

    print(f"⬇️ Güncelleme indiriliyor...")

    request = urllib.request.Request(
        url,
        headers=github_headers(
            accept="application/octet-stream"
        ),
        method="GET",
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:

        with open(destination, "wb") as f:
            shutil.copyfileobj(
                response,
                f
            )


# ============================================================
# SHA-256
# ============================================================

def calculate_sha256(path):

    sha256 = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def verify_checksum(
    file_path,
    expected_digest
):

    if not expected_digest:

        print(
            "⚠️ Release asset SHA-256 digest içermiyor."
        )

        return False

    if not expected_digest.startswith(
        "sha256:"
    ):

        print(
            "❌ Desteklenmeyen digest formatı."
        )

        return False

    expected = expected_digest.split(
        ":",
        1
    )[1]

    actual = calculate_sha256(
        file_path
    )

    print(
        f"Beklenen SHA-256: {expected}"
    )

    print(
        f"Hesaplanan SHA-256: {actual}"
    )

    if actual != expected:

        print(
            "❌ SHA-256 doğrulaması başarısız!"
        )

        return False

    print(
        "✅ SHA-256 doğrulaması başarılı."
    )

    return True


# ============================================================
# YENİ SÜRÜMÜ KUR
# ============================================================

def install_version(
    zip_path,
    version
):

    target_dir = (
        VERSIONS_DIR / version
    )

    if target_dir.exists():

        print(
            f"⚠️ {version} zaten mevcut."
        )

        return target_dir

    temporary_dir = (
        VERSIONS_DIR
        / f".{version}.installing"
    )

    if temporary_dir.exists():

        shutil.rmtree(
            temporary_dir
        )

    temporary_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        f"📦 Yeni sürüm hazırlanıyor: {version}"
    )

    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as z:

        z.extractall(
            temporary_dir
        )

    entries = list(
        temporary_dir.iterdir()
    )

    if (
        len(entries) == 1
        and entries[0].is_dir()
    ):

        source_dir = entries[0]

        for item in source_dir.iterdir():

            shutil.move(
                str(item),
                str(
                    temporary_dir
                    / item.name
                )
            )

        source_dir.rmdir()

    temporary_dir.rename(
        target_dir
    )

    print(
        f"✅ {version} kurulumu tamamlandı."
    )

    return target_dir


# ============================================================
# SAĞLIK KONTROLÜ
# ============================================================

def health_check(version_dir):

    print(
        "🔎 Yeni sürüm kontrol ediliyor..."
    )

    version_file = (
        version_dir / "version.json"
    )

    if not version_file.exists():

        print(
            "❌ version.json bulunamadı."
        )

        return False

    try:

        with open(
            version_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if "version" not in data:

            print(
                "❌ version.json içinde version alanı yok."
            )

            return False

    except Exception as e:

        print(
            f"❌ version.json okunamadı: {e}"
        )

        return False

    print(
        "✅ Temel sağlık kontrolü başarılı."
    )

    return True


# ============================================================
# SÜRÜMÜ AKTİF ET
# ============================================================

def activate_version(version):

    target = (
        VERSIONS_DIR / version
    )

    if not target.exists():

        print(
            "❌ Aktivasyon başarısız: "
            "hedef sürüm bulunamadı."
        )

        return False

    temporary_link = (
        BASE_DIR / "current.new"
    )

    if (
        temporary_link.exists()
        or temporary_link.is_symlink()
    ):

        temporary_link.unlink()

    temporary_link.symlink_to(
        target
    )

    temporary_link.replace(
        CURRENT_LINK
    )

    print(
        f"✅ Aktif sürüm artık: {version}"
    )

    return True


# ============================================================
# GÜNCELLEME
# ============================================================

def update():

    current_version = (
        get_current_version()
    )

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

        print(
            "✅ Güncelleme gerekmiyor."
        )

        return

    print(
        f"🚀 Yeni sürüm bulundu: "
        f"{latest_version}"
    )

    asset = find_release_asset(
        release
    )

    if not asset:

        print(
            "❌ Release içerisinde "
            "uygulama ZIP dosyası bulunamadı."
        )

        return

    asset_name = asset["name"]

    expected_digest = asset.get(
        "digest"
    )

    # Private repository için
    # browser_download_url yerine
    # GitHub API asset URL'sini kullanıyoruz.
    asset_api_url = asset["url"]

    print(
        f"📦 Asset: {asset_name}"
    )

    with tempfile.TemporaryDirectory() as temp:

        zip_path = (
            Path(temp)
            / asset_name
        )

        download_file(
            asset_api_url,
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

        version = (
            latest_version
            .lstrip("v")
        )

        new_version_dir = (
            install_version(
                zip_path,
                version
            )
        )

        if not health_check(
            new_version_dir
        ):

            print(
                "❌ Yeni sürüm sağlık "
                "kontrolünü geçemedi."
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

    print(
        "\n🎉 Güncelleme tamamlandı!"
    )

    print(
        "ℹ️ Servis yeniden başlatma "
        "bir sonraki aşamada eklenecek."
    )


# ============================================================
# PROGRAM
# ============================================================

if __name__ == "__main__":

    try:

        update()

    except Exception as e:

        print(
            f"❌ Güncelleme sırasında hata: {e}"
        )