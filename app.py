import os
import sys
import requests
import gradio as gr
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Lädt die Umgebungsvariablen aus der .env-Datei im aktuellen Verzeichnis
load_dotenv()

def check_api_status():
    """
    Klick-Prüfung: Setzt eine minimale GET-Anfrage an ein schnelles Textmodell ab.
    Verhindert den Status 405 und prüft die Erreichbarkeit deines Keys.
    """
    api_key = os.getenv("POLLINATIONS_API_KEY")
    if not api_key or "dein_schlüssel" in api_key:
        return "❌ Fehler: Kein gültiger API-Schlüssel in der .env-Datei!"

    # Verwende den offiziellen GET-Endpoint für Textmodelle, um 405-Fehler zu vermeiden
    base_url = "https://pollinations.ai"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    params = {
        "model": "openai",
        "json": "true"
    }

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            return "🟢 API online! Die Verbindung steht und dein Key ist gültig."
        elif response.status_code == 402:
            return "🛑 Spore-Limit aktiv: Verbindung steht, aber dein stündliches Guthaben ist leer."
        elif response.status_code == 401:
            return "❌ API-Fehler 401: Dein API-Key ist ungültig oder abgelaufen."
        else:
            return f"⚠️ API antwortet mit Status {response.status_code}. Bitte später versuchen."

    except requests.exceptions.RequestException:
        return "🛑 API blockiert aktuell (ConnectionError). Dein stündliches Spore-Guthaben ist aufgebraucht!"


def generate_image_web(prompt: str, width: int, height: int, model: str, remove_logo: bool):
    """
    Hauptfunktion zur Bildgenerierung über den offiziellen GET-Pfad-Endpoint.
    """
    api_key = os.getenv("POLLINATIONS_API_KEY")
    if not api_key or "dein_schlüssel" in api_key:
        return None, "❌ Fehler: Kein gültiger API-Schlüssel in der .env-Datei gefunden!"

    if not prompt.strip():
        return None, "⚠️ Hinweis: Bitte gib eine Bildbeschreibung ein."

    # Sonder- und Leerzeichen im Eingabetext schützen
    encoded_prompt = requests.utils.quote(prompt)

    # 1. FIX: "gen." Subdomain hinzugefügt!
    base_url = f"https://gen.pollinations.ai/image/{encoded_prompt}"

    # 2. FIX: Den Key zusätzlich als Query-Parameter anhängen,
    # da GET-Bildpfade den Key dort am sichersten auslesen.
    params = {
        "key": api_key,
        "model": model,
        "width": width,
        "height": height,
        "nologo": "true" if remove_logo else "false"
    }

    try:
        # Wir senden die Anfrage mit den korrigierten Parametern an die gen.-Domain
        response = requests.get(base_url, params=params, timeout=45)
        content_type = response.headers.get('Content-Type', '')

        if response.status_code == 200 and 'image' in content_type:
            img = Image.open(BytesIO(response.content))
            return img, "🟢 Bild erfolgreich generiert!"
        elif response.status_code == 402:
            return None, "🛑 Spore-Limit erreicht! Stündliches Guthaben leer."
        else:
            error_details = response.text[:150] if "text" in content_type else "Keine Details"
            return None, f"❌ API-Fehler (Status {response.status_code}): {error_details}"

    except requests.exceptions.RequestException:
        return None, "🛑 Verbindung getrennt (ConnectionError). Dein stündliches Guthaben ist leer oder der Server ist überlastet."


# --- GRADIO BENUTZEROBERFLÄCHE ---
with gr.Blocks(title="Pollinations AI Studio") as demo:

    gr.Markdown(
        """
        # 🎨 Pollinations AI Image Studio
        Generiere Bilder über die offizielle API. Nutze den Diagnose-Button, um deine Leitung und dein Guthaben live zu prüfen.
        """
    )

    with gr.Row():
        # Linke Spalte: Eingaben und Einstellungen
        with gr.Column(scale=1):
            prompt_input = gr.Textbox(
                label="Bildbeschreibung (Prompt)",
                placeholder="Ein futuristischer Cyberpunk-Garten im Neonlicht...",
                lines=3
            )

            with gr.Accordion("Erweiterte Einstellungen", open=False):
                model_dropdown = gr.Dropdown(
                    choices=["flux", "turbo"],
                    value="flux",
                    label="KI-Modell"
                )

                with gr.Row():
                    width_slider = gr.Slider(
                        minimum=256, maximum=1440, step=64, value=1024, label="Breite"
                    )
                    height_slider = gr.Slider(
                        minimum=256, maximum=1440, step=64, value=1024, label="Höhe"
                    )

                logo_checkbox = gr.Checkbox(
                    value=True, label="Wasserzeichen (Logo) entfernen"
                )

            generate_btn = gr.Button("🚀 Bild generieren", variant="primary")

            gr.Markdown("---")

            # Diagnose-Sektion
            test_conn_btn = gr.Button("🔍 API- & Guthaben-Verbindung prüfen", variant="secondary")
            status_output = gr.Textbox(
                label="System-Status / Guthaben-Warnung",
                value="Bereit. Nutze den Button oben für einen Schnelltest.",
                interactive=False
            )

        # Rechte Spalte: Bild-Ausgabe
        with gr.Column(scale=1):
            image_output = gr.Image(label="Generiertes Bild", type="pil")

    # Event 1: Bild generieren
    generate_btn.click(
        fn=generate_image_web,
        inputs=[prompt_input, width_slider, height_slider, model_dropdown, logo_checkbox],
        outputs=[image_output, status_output]
    )

    # Event 2: Manuelle Prüfung über den dedizierten Button
    test_conn_btn.click(
        fn=check_api_status,
        inputs=None,
        outputs=status_output
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), share=True)
