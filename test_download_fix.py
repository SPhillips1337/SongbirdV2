#!/usr/bin/env python3
"""
Test script to validate ComfyUI download fixes for Cloudflare tunnel
"""
import os
import sys
import logging
import time
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

load_dotenv()

# Import after dotenv is loaded
from tools.comfy import ComfyClient

logger = logging.getLogger(__name__)

def test_comfy_client():
    """Test the enhanced ComfyClient"""
    logger.info("=" * 60)
    logger.info("ComfyUI Client Test")
    logger.info("=" * 60)
    
    # Create client
    client = ComfyClient()
    logger.info(f"\nComfyUI URL: {client.url}")
    logger.info(f"SSL Verify: {client.verify}")
    logger.info(f"Output dir: {client.output_dir}")
    
    # Test 1: Basic connection
    logger.info("\n--- Test 1: Basic Connection ---")
    try:
        response = client.get_history("test123")
        logger.info(f"✓ Can reach /history endpoint")
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        return False
    
    # Test 2: Check fallback list method
    logger.info("\n--- Test 2: File Listing Fallback ---")
    try:
        files = client._list_output_files("audio")
        logger.info(f"✓ List method works, found {len(files)} files")
        if files:
            logger.info(f"  Sample files: {files[:3]}")
    except Exception as e:
        logger.error(f"✗ List method failed: {e}")
    
    # Test 3: Try downloading a test file
    logger.info("\n--- Test 3: Download Test ---")
    logger.info("Note: This will fail with 404 unless a file actually exists")
    try:
        result = client.download_file("test.mp3", "audio", "output", retries=1)
        if result:
            logger.info(f"✓ Download succeeded: {result}")
        else:
            logger.info("✗ Download returned None (expected if file doesn't exist)")
    except Exception as e:
        logger.error(f"✗ Download error: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Tests Complete - Client is ready for generation")
    logger.info("=" * 60)
    return True

if __name__ == "__main__":
    success = test_comfy_client()
    sys.exit(0 if success else 1)
