import os
import requests
import gradio as gr
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Lädt den API-Schlüssel aus der .env-Datei
load_dotenv()

def generate_image_web(prompt: str, width: int, height: int, model: str, remove_logo: bool):
    """
    Schnittstellen-Funktion für das Gradio Web-Interface.
    Gibt das fertige Bild oder eine Fehlermeldung zurück.
    """
    api_key = os.getenv("POLLINATIONS_API_KEY")

    if not api_key or "dein_schlüssel" in api_key:
        raise gr.Error("Kein gültiger API-Schlüssel in der .env-Datei gefunden!")

    if not prompt.strip():
        raise gr.Error("Bitte gib eine Bildbeschreibung ein.")

    # URL-Encoding für den Prompt
    encoded_prompt = requests.utils.quote(prompt)
    base_url = f"https://pollinations.ai{encoded_prompt}"

    # HTTP-Header für die Authentifizierung
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    # Parameter aus der UI übernehmen
    params = {
        "model": model,
        "width": width,
        "height": height,
        "nologo": "true" if remove_logo else "false"
    }

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=45)
        content_type = response.headers.get('Content-Type', '')

        if response.status_code == 200 and 'image' in content_type:
            # Bild erfolgreich geladen
            img = Image.open(BytesIO(response.content))
            return img
        else:
            # Fehlermeldung aufbereiten
            error_msg = f"API-Fehler (Status {response.status_code})"
            if "text" in content_type:
                error_msg += f": {response.text[:100]}"
            raise gr.Error(error_msg)

    except requests.exceptions.RequestException as e:
        raise gr.Error(f"Netzwerkfehler: {e.__class__.__name__}")

# --- GRADIO BENUTZEROBERFLÄCHE BAUEN ---
with gr.Blocks(theme=gr.themes.Soft(), title="Pollinations AI Studio") as demo:

    gr.Markdown(
        """
        # 🎨 Pollinations AI Image Studio
        Generiere atemberaubende Bilder mit modernsten KI-Modellen über die offizielle Pollinations API.
        """
    )

    with gr.Row():
        # Linke Spalte: Steuerungen
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

        # Rechte Spalte: Ergebnisanzeige
        with gr.Column(scale=1):
            image_output = gr.Image(label="Generiertes Bild", type="pil")

    # Event-Verknüpfung beim Klick auf den Button
    generate_btn.click(
        fn=generate_image_web,
        inputs=[prompt_input, width_slider, height_slider, model_dropdown, logo_checkbox],
        outputs=image_output
    )

if __name__ == "__main__":
    # share=True generiert einen öffentlichen Link, der 72 Stunden gültig bleibt!
    demo.launch(share=True)
