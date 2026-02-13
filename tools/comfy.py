import requests
import json
import time
import os
import logging

class ComfyClient:
    def __init__(self, url=None, output_dir="output", timeout=30):
        self.url = url or os.getenv("COMFYUI_URL", "http://localhost:8188")
        self.output_dir = output_dir
        self.timeout = timeout
        os.makedirs(self.output_dir, exist_ok=True)

    def submit_prompt(self, lyrics, tags, bpm=120, keyscale="C major", duration=240, filename_prefix="songbird", seed=None, steps=8, cfg=1, sampler_name="euler", scheduler="simple", negative_prompt=""):
        # Load workflow template
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, "audio_ace_step_1_5_checkpoint.json")

        try:
            with open(template_path, "r") as f:
                prompt = json.load(f)
        except Exception as e:
            logging.error(f"Error loading workflow template: {e}")
            return None

        generation_seed = seed if seed is not None else int(time.time())

        # Update KSampler (Node 3)
        if "3" in prompt:
            inputs = prompt["3"]["inputs"]
            inputs["seed"] = generation_seed
            inputs["steps"] = steps
            inputs["cfg"] = cfg
            inputs["sampler_name"] = sampler_name
            inputs["scheduler"] = scheduler

        # Update TextEncodeAceStepAudio1.5 (Node 94)
        if "94" in prompt:
            inputs = prompt["94"]["inputs"]
            inputs["tags"] = tags
            inputs["lyrics"] = lyrics
            inputs["seed"] = generation_seed
            inputs["bpm"] = bpm
            inputs["duration"] = duration
            inputs["keyscale"] = keyscale

        # Update EmptyAceStep1.5LatentAudio (Node 98)
        if "98" in prompt:
            prompt["98"]["inputs"]["seconds"] = duration

        # Update SaveAudioMP3 (Node 104)
        if "104" in prompt:
            prompt["104"]["inputs"]["filename_prefix"] = f"audio/{filename_prefix}"

        # Handle Negative Prompt
        if negative_prompt:
            # Create negative node (105)
            negative_node = {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["97", 1]
                },
                "class_type": "CLIPTextEncode"
            }
            prompt["105"] = negative_node

            # Point KSampler negative input to this node
            if "3" in prompt:
                prompt["3"]["inputs"]["negative"] = ["105", 0]
        else:
            # Ensure it points to ZeroOut (47)
            if "3" in prompt:
                prompt["3"]["inputs"]["negative"] = ["47", 0]

        try:
            response = requests.post(f"{self.url}/prompt", json={"prompt": prompt}, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if "WRONG_VERSION_NUMBER" in str(e):
                logging.error(f"Error submitting to ComfyUI: SSL Error (Wrong Version). TIP: You are likely using 'https://' for a server that only supports 'http://'. Please check COMFYUI_URL in .env.")
            else:
                logging.error(f"Error submitting to ComfyUI: {e}")
            return None

    def get_history(self, prompt_id):
        try:
            response = requests.get(f"{self.url}/history/{prompt_id}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching ComfyUI history: {e}")
            return None

    def wait_and_download_output(self, prompt_id, timeout=600):
        """Polls history and downloads the generated file."""
        logging.info(f"Waiting for generation (Prompt ID: {prompt_id})...")
        start_time = time.time()
        while True:
            history = self.get_history(prompt_id)
            if history and prompt_id in history:
                break

            if time.time() - start_time > timeout:
                logging.error(f"Timeout waiting for generation (Prompt ID: {prompt_id})")
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
            logging.error("No output files found in history.")
            return None

        # Download the first file
        file_info = files[0]
        if not file_info or not isinstance(file_info, dict):
            logging.error("Invalid file info found in history.")
            return None

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
            response = requests.get(f"{self.url}/view", params=params, timeout=self.timeout)
            response.raise_for_status()

            # Save to local output dir
            # Sanitize filename to prevent path traversal
            safe_filename = os.path.basename(filename)
            local_path = os.path.join(self.output_dir, safe_filename)

            with open(local_path, "wb") as f:
                f.write(response.content)

            logging.info(f"Saved generated audio to {local_path}")
            return local_path
        except Exception as e:
            logging.error(f"Error downloading file: {e}")
            return None
