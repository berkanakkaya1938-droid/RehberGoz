import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "gemini-3.1-flash-lite"


def main():
    if not API_KEY:
        print("❌ Gemini API key bulunamadı!")
        return

    with open("test_camera.jpg", "rb") as f:
        image_bytes = f.read()

    print(f"📸 Görüntü okundu: {len(image_bytes)} bytes")

    client = genai.Client(api_key=API_KEY)

    print("☁️ Gemini'ye görüntü gönderiliyor...")

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"
            ),
            (
                "Bu görüntüyü dikkatlice analiz et. "
                "Görüntüde ne görüyorsun? "
                "Özellikle insanları ve nesneleri belirt."
            )
        ]
    )

    print("\n🤖 Gemini'nin cevabı:\n")
    print(response.text)

    print("\n✅ Test tamamlandı.")


if __name__ == "__main__":
    main()
