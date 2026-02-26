import requests
import json
import time
import os
import re
import config
import logging
import uuid
import websocket
import ssl
from urllib.parse import urlparse

class ComfyClient:
    def __init__(self, url=None, output_dir="output", timeout=120):
        self.url = url or os.getenv("COMFYUI_URL", "http://localhost:8188")
        self.output_dir = output_dir
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())
        
        # SSL Verification Bypass support for Cloudflare Tunnels/Remote Servers
        verify_ssl = os.getenv("COMFYUI_VERIFY_SSL", "true").lower()
        self.verify = verify_ssl == "true"
        
        if not self.verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logging.info("COMFYUI_VERIFY_SSL is False: SSL verification disabled for ComfyUI.")

        os.makedirs(self.output_dir, exist_ok=True)

    def submit_prompt(self, lyrics, tags, bpm=120, keyscale="C major", duration=240, filename_prefix="songbird", seed=None, steps=50, cfg=4.0, sampler_name="euler", scheduler="sgm_uniform", negative_prompt="", min_p=0, cfg_scale=4.0):
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
            inputs["min_p"] = min_p
            inputs["cfg_scale"] = cfg_scale

        # Update EmptyAceStep1.5LatentAudio (Node 98)
        if "98" in prompt:
            prompt["98"]["inputs"]["seconds"] = duration

        # Update SaveAudioMP3 (Node 104)
        if "104" in prompt:
            prompt["104"]["inputs"]["filename_prefix"] = f"audio/{filename_prefix}"

        # Handle Negative Prompt
        # Uses CLIPTextEncode (Node 7) instead of ConditioningZeroOut
        # Note: We previously used ConditioningZeroOut but it caused sound quality issues
        # by effectively combining negative and positive prompts
        neg_node_id = getattr(config, "NEGATIVE_PROMPT_NODE_ID", "7")
        if neg_node_id in prompt:
            prompt[neg_node_id]["inputs"]["text"] = negative_prompt
        else:
            logging.warning(f"Negative prompt node {neg_node_id} not found in workflow.")

        try:
            response = requests.post(
                f"{self.url}/prompt", 
                json={"prompt": prompt, "client_id": self.client_id}, 
                timeout=self.timeout,
                verify=self.verify
            )
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
            response = requests.get(
                f"{self.url}/history/{prompt_id}", 
                timeout=self.timeout,
                verify=self.verify
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching ComfyUI history: {e}")
            return None

    def wait_and_download_output(self, prompt_id, timeout=1200):
        """Monitors WebSocket for completion and downloads the generated file."""
        logging.info(f"Connecting to WebSocket for monitoring (Prompt ID: {prompt_id})...")
        
        ws_protocol = "wss" if self.url.startswith("https") else "ws"
        # Extract host from URL
        parsed_url = urlparse(self.url)
        host = parsed_url.netloc
        
        ws_url = f"{ws_protocol}://{host}/ws?clientId={self.client_id}"
        
        success = False
        try:
            ws = websocket.WebSocket()
            # Set timeout for the WebSocket connection itself
            ws.settimeout(30) # Connection timeout
            
            # Respect SSL verification setting
            sslopt = {"cert_reqs": ssl.CERT_NONE} if not self.verify else {}
            
            ws.connect(ws_url, sslopt=sslopt)
            logging.info(f"WebSocket connected. Monitoring execution...")
            
            # Reset timeout for monitoring phase
            ws.settimeout(timeout)
            
            start_time = time.time()
            while True:
                try:
                    out = ws.recv()
                    if not out:
                        continue
                    
                    if isinstance(out, str):
                        message = json.loads(out)
                        if message['type'] == 'executing':
                            data = message['data']
                            # When node is None and the prompt_id matches, the workflow has finished
                            if data['node'] is None and data['prompt_id'] == prompt_id:
                                logging.info("Execution complete via WebSocket signal.")
                                success = True
                                break 
                    
                except websocket.WebSocketTimeoutException:
                     if time.time() - start_time > timeout:
                        logging.error(f"Timeout waiting for WebSocket message (Prompt ID: {prompt_id})")
                        break
                except Exception as e:
                    logging.warning(f"WebSocket error during receive: {e}")
                    break

            ws.close()
        except Exception as e:
            logging.error(f"Failed to connect or monitor via WebSocket: {e}. Falling back to standard polling...")

        if not success:
            logging.info(f"WebSocket monitoring failed or timed out. Falling back to HTTP polling for Prompt ID: {prompt_id}")
            start_time = time.time()
            while True:
                history = self.get_history(prompt_id)
                if history and prompt_id in history:
                    logging.info("Generation complete (verified via history polling).")
                    success = True
                    break
                
                if time.time() - start_time > timeout:
                    logging.error(f"Timeout waiting for generation (Prompt ID: {prompt_id})")
                    return self._fallback_download(prompt_id)
                
                time.sleep(5)

        # Retrieve history to get output information
        history = self.get_history(prompt_id)
        if not history or prompt_id not in history:
            logging.error(f"Could not retrieve history for Prompt ID {prompt_id} after completion.")
            return self._fallback_download(prompt_id)

        # Extract filename
        outputs = history[prompt_id].get("outputs", {})
        
        # Find the output from SaveAudioMP3 node (ID 104)
        node_output = outputs.get("104")
        
        if not node_output:
            logging.warning(f"Node 104 not found in outputs for Prompt ID {prompt_id}. Searching all nodes for audio output...")
            # Fallback: Search all nodes for anything that looks like audio output
            for node_id, data in outputs.items():
                if isinstance(data, dict) and any(k in str(data).lower() for k in ["audio", "mp3", "wav"]):
                    logging.info(f"Potential audio output found in Node {node_id}")
                    node_output = data
                    break
                elif isinstance(data, list) and len(data) > 0:
                    if any(isinstance(f, dict) and "filename" in f for f in data):
                         logging.info(f"Found files list in Node {node_id}")
                         node_output = data
                         break

        if not node_output:
            logging.error(f"No output files found in history for Prompt ID {prompt_id}. Available nodes: {list(outputs.keys())}")
            return self._fallback_download(prompt_id)

        files = []
        if isinstance(node_output, list):
            files.extend(node_output)
        elif isinstance(node_output, dict):
            for key, val in node_output.items():
                if isinstance(val, list):
                    files.extend(val)

        if not files:
            logging.error("No output files found in history.")
            return self._fallback_download(prompt_id)

        # Download the first file
        file_info = files[0]
        if not file_info or not isinstance(file_info, dict):
            logging.error("Invalid file info found in history.")
            return self._fallback_download(prompt_id)

        filename = file_info.get("filename")
        subfolder = file_info.get("subfolder", "")
        folder_type = file_info.get("type", "output")

        return self.download_file(filename, subfolder, folder_type)

    def _fallback_download(self, prompt_id):
        """Fallback method to download when history API fails (Cloudflare tunnel issue)."""
        logging.info(f"Using fallback download for Prompt ID: {prompt_id}")
        
        # First, try to list audio files from output directory and download the most recent
        logging.warning("History API unavailable (likely Cloudflare tunnel issue). Attempting to find recently generated file...")
        audio_files = self._list_output_files("audio")
        
        if audio_files:
            logging.info(f"Found {len(audio_files)} potential audio files")
            for filename in audio_files[:5]:  # Try up to 5 files
                try:
                    logging.info(f"Attempting to download: {filename}")
                    result = self.download_file(filename, "audio", "output")
                    if result:
                        logging.info(f"✓ Successfully downloaded via directory listing: {result}")
                        return result
                except Exception as e:
                    logging.debug(f"Could not download {filename}: {e}")
        
        # Fallback: Try common ComfyUI naming patterns
        logging.warning("Directory listing failed. Trying common filename patterns...")
        common_patterns = [
            ("ComfyUI_00001.mp3", "audio", "output"),
            ("ComfyUI_00001.wav", "audio", "output"),
            ("songbird.mp3", "audio", "output"),
            ("songbird.wav", "audio", "output"),
        ]
        
        for filename, subfolder, folder_type in common_patterns:
            try:
                logging.info(f"Trying pattern: {filename}")
                result = self.download_file(filename, subfolder, folder_type)
                if result:
                    logging.info(f"✓ Successfully downloaded via fallback pattern: {result}")
                    return result
            except Exception as e:
                logging.debug(f"Fallback pattern {filename} failed: {e}")
        
        logging.error("All fallback methods exhausted. Could not download generated file.")
        return None

    def _list_output_files(self, subfolder="audio"):
        """Attempt to list files in a given output subfolder."""
        try:
            logging.info(f"Attempting to list files in {subfolder}/...")
            
            # Try to access the files directly via web interface
            # This is a fallback that might work if the /view endpoint supports directory listing
            response = requests.get(
                f"{self.url}/",
                timeout=self.timeout,
                verify=self.verify
            )
            
            # Look for audio file links in the HTML
            import re
            pattern = r'href=["\']/view\?[^"\']*filename=([^&\'"]+)[^"\']*["\']'
            matches = re.findall(pattern, response.text)
            
            if matches:
                logging.info(f"Found {len(matches)} files in web interface")
                # Filter for audio files
                audio_files = [f for f in matches if f.endswith(('.mp3', '.wav', '.flac'))]
                return audio_files[:5]  # Return first 5 to avoid too many attempts
            
        except Exception as e:
            logging.debug(f"Could not list files: {e}")
        
        return []

    def download_file(self, filename, subfolder, folder_type, retries=3):
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        
        for attempt in range(retries):
            try:
                logging.info(f"Downloading file: {filename} (subfolder={subfolder}, type={folder_type}) - Attempt {attempt + 1}/{retries}")
                response = requests.get(
                    f"{self.url}/view", 
                    params=params, 
                    timeout=self.timeout,
                    verify=self.verify,
                    allow_redirects=True
                )
                
                # Log detailed response info for debugging
                logging.debug(f"Response status: {response.status_code}")
                logging.debug(f"Response headers: {dict(response.headers)}")
                logging.debug(f"Content length: {len(response.content)}")
                
                if response.status_code == 404:
                    logging.warning(f"File not found (404): {filename}")
                    if attempt < retries - 1:
                        logging.info("Retrying...")
                        time.sleep(2)
                        continue
                    return None
                    
                response.raise_for_status()

                # Verify we got actual content
                if len(response.content) == 0:
                    logging.warning(f"Downloaded file is empty (0 bytes)")
                    if attempt < retries - 1:
                        logging.info("Retrying...")
                        time.sleep(2)
                        continue
                    return None

                # Save to local output dir
                # Sanitize filename to prevent path traversal
                safe_filename = os.path.basename(filename)
                local_path = os.path.join(self.output_dir, safe_filename)

                with open(local_path, "wb") as f:
                    f.write(response.content)

                file_size = os.path.getsize(local_path)
                logging.info(f"✓ Successfully saved generated audio: {local_path} (Size: {file_size} bytes)")
                return local_path
                
            except requests.exceptions.Timeout:
                logging.warning(f"Download timeout (attempt {attempt + 1}/{retries}): {filename}")
                if attempt < retries - 1:
                    logging.info("Retrying after delay...")
                    time.sleep(5)
                    continue
                return None
                
            except requests.exceptions.ConnectionError as e:
                logging.warning(f"Connection error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    logging.info("Retrying after delay...")
                    time.sleep(5)
                    continue
                return None
                    
            except Exception as e:
                logging.error(f"Error downloading file (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    logging.info("Retrying...")
                    time.sleep(2)
                    continue
                return None
        
        logging.error(f"Failed to download {filename} after {retries} attempts")
        return None
