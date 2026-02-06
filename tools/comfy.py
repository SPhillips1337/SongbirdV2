import requests
import json
import time
import os

class ComfyClient:
    def __init__(self, url=None):
        self.url = url or os.getenv("COMFYUI_URL", "http://localhost:8188")
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def submit_prompt(self, lyrics, tags, bpm=120, keyscale="C major", duration=240, filename_prefix="songbird"):
        # ACE Step 1.5 Workflow structure from audio_ace_step_1_5_checkpoint.json
        prompt = {
            "3": {
                "inputs": {
                    "seed": int(time.time()),
                    "steps": 8,
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "model": ["78", 0],
                    "positive": ["94", 0],
                    "negative": ["47", 0],
                    "latent_image": ["98", 0]
                },
                "class_type": "KSampler"
            },
            "18": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["97", 2]
                },
                "class_type": "VAEDecodeAudio"
            },
            "47": {
                "inputs": {
                    "conditioning": ["94", 0]
                },
                "class_type": "ConditioningZeroOut"
            },
            "78": {
                "inputs": {
                    "shift": 3,
                    "model": ["97", 0]
                },
                "class_type": "ModelSamplingAuraFlow"
            },
            "94": {
                "inputs": {
                    "tags": tags,
                    "lyrics": lyrics,
                    "seed": int(time.time()),
                    "bpm": bpm,
                    "duration": duration,
                    "timesignature": "4",
                    "language": "en",
                    "keyscale": keyscale,
                    "generate_audio_codes": True,
                    "cfg_scale": 2,
                    "temperature": 0.85,
                    "top_p": 0.9,
                    "top_k": 0,
                    "clip": ["97", 1]
                },
                "class_type": "TextEncodeAceStepAudio1.5"
            },
            "97": {
                "inputs": {
                    "ckpt_name": "ace_step_1.5_turbo_aio.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "98": {
                "inputs": {
                    "seconds": duration,
                    "batch_size": 1
                },
                "class_type": "EmptyAceStep1.5LatentAudio"
            },
            "104": {
                "inputs": {
                    "filename_prefix": f"audio/{filename_prefix}",
                    "quality": "V0",
                    "audioUI": "",
                    "audio": ["18", 0]
                },
                "class_type": "SaveAudioMP3"
            }
        }

        try:
            response = requests.post(f"{self.url}/prompt", json={"prompt": prompt})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if "WRONG_VERSION_NUMBER" in str(e):
                print(f"Error submitting to ComfyUI: SSL Error (Wrong Version). TIP: You are likely using 'https://' for a server that only supports 'http://'. Please check COMFYUI_URL in .env.")
            else:
                print(f"Error submitting to ComfyUI: {e}")
            return None

    def get_history(self, prompt_id):
        try:
            response = requests.get(f"{self.url}/history/{prompt_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching ComfyUI history: {e}")
            return None

    def wait_and_download_output(self, prompt_id, timeout=600):
        """Polls history and downloads the generated file."""
        print(f"Waiting for generation (Prompt ID: {prompt_id})...")
        start_time = time.time()
        while True:
            history = self.get_history(prompt_id)
            if history and prompt_id in history:
                break

            if time.time() - start_time > timeout:
                print(f"Timeout waiting for generation (Prompt ID: {prompt_id})")
                return None

            time.sleep(2)

        # Extract filename
        outputs = history[prompt_id].get("outputs", {})
        # Find the output from SaveAudioMP3 node (ID 104)
        node_output = outputs.get("104", {})

        files = []
        if isinstance(node_output, list):
            files.extend(node_output)
        elif isinstance(node_output, dict):
            for key, val in node_output.items():
                if isinstance(val, list):
                    files.extend(val)

        if not files:
            print("No output files found in history.")
            return None

        # Download the first file
        file_info = files[0]
        filename = file_info.get("filename")
        subfolder = file_info.get("subfolder", "")
        folder_type = file_info.get("type", "output")

        return self.download_file(filename, subfolder, folder_type)

    def download_file(self, filename, subfolder, folder_type):
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        try:
            response = requests.get(f"{self.url}/view", params=params)
            response.raise_for_status()

            # Save to local output dir
            local_path = os.path.join(self.output_dir, filename)

            with open(local_path, "wb") as f:
                f.write(response.content)

            print(f"Saved generated audio to {local_path}")
            return local_path
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
