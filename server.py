import litserve as ls
from piper import PiperVoice
import os
import io
import wave
from fastapi import Response, HTTPException
from pydub import AudioSegment
from dotenv import load_dotenv
import glob
import uuid
import torch

load_dotenv()


class PiperTTSAPI(ls.LitAPI):
    def setup(self, device):
        """Load all available models from the ./models directory.
        Models are stored in a dict ``self.models`` keyed by the base filename
        (without the .onnx extension). The default model can still be set via
        ``DEFAULT_PIPER_MODEL`` environment variables.
        """
        self.models = {}
        models_dir = os.path.join(os.path.dirname(__file__), "models")
        # Scan for *.onnx files and load corresponding config
        for onnx_path in glob.glob(os.path.join(models_dir, "*.onnx")):
            base = os.path.splitext(os.path.basename(onnx_path))[0]
            json_path = onnx_path + ".json"
            if not os.path.exists(json_path):
                continue
            try:
                self.models[base] = PiperVoice.load(onnx_path, config_path=json_path)
                print(f"Loaded model '{base}' from {onnx_path}")
            except Exception as e:
                print(f"Failed to load model {base}: {e}")

        # Store a reference to the default model name (first loaded if not set)
        self.default_model = next(iter(self.models)) if self.models else None

        use_cuda = torch.cuda.is_available()
        if use_cuda:
            print("CUDA is available, GPU acceleration is enabled")

        self.use_cuda = use_cuda

    def decode_request(self, request):
        """Validate and extract request parameters.
        Expected fields:
          - input (str): text to synthesize (required)
          - model (str): optional model name (defaults to default model)
          - response_format (str): "mp3" (default) or "wav"
        """
        if "input" not in request:
            raise HTTPException(status_code=400, detail="Missing 'input' field.")
        model_name = request.get("model") or self.default_model
        if not model_name:
            raise HTTPException(
                status_code=400,
                detail="No model specified and no default model available.",
            )
        response_format = request.get("response_format", "mp3").lower()
        if response_format not in ("mp3", "wav"):
            raise HTTPException(
                status_code=400,
                detail="Unsupported response_format. Use 'mp3' or 'wav'.",
            )
        self.response_format = response_format
        return {
            "text": request["input"],
            "model": model_name,
            "response_format": response_format,
        }

    def predict(self, inputs):
        text = inputs["text"]
        model_name = inputs["model"]
        # Retrieve the appropriate PiperVoice instance
        if model_name not in self.models:
            raise HTTPException(
                status_code=400, detail=f"Model '{model_name}' not found."
            )
        voice_obj = self.models[model_name]
        output_path = f"output/output_{uuid.uuid4()}.wav"
        # Synthesize to a WAV buffer with proper header
        with wave.open(output_path, "wb") as wav_file:
            voice_obj.synthesize_wav(text, wav_file, use_cuda=self.use_cuda)
        return output_path

    def encode_response(self, wav_path):
        """Encode the raw WAV bytes to the requested format.
        Uses the response format stored during decode (self.response_format).
        If ``self.response_format`` is "wav", returns raw WAV bytes.
        Otherwise converts to MP3 using pydub.
        """

        # load file
        audio = AudioSegment.from_wav(wav_path)

        # Clean up
        os.remove(wav_path)

        response_format = getattr(self, "response_format", "mp3")
        if response_format == "wav":
            return Response(content=audio.raw_data, media_type="audio/wav")
        # Convert WAV to MP3
        try:
            mp3_io = io.BytesIO()
            audio.export(mp3_io, format="mp3")
            return Response(content=mp3_io.getvalue(), media_type="audio/mpeg")
        except Exception as e:
            print(f"Audio conversion failed: {e}")
            raise HTTPException(status_code=500, detail="Audio conversion failed")


if __name__ == "__main__":
    api = PiperTTSAPI(api_path="/v1/audio/speech")
    server = ls.LitServer(
        api,
        accelerator="auto",
    )

    @server.app.get("/health")
    async def health():
        return "ok"

    server.run(port=os.getenv("PORT", 8000), generate_client_file=False)
