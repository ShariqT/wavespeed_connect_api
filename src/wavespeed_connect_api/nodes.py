from inspect import cleandoc
import requests
import json


class WaveSpeedReferenceToVideo:
    """
    A ComfyUI node that connects to the WaveSpeed AI API for reference-to-video generation.
    Uses the Seedance 2.5 Flash model to generate videos from reference images and videos.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        """
        Return a dictionary which contains config for all input fields.
        """
        return {
            "required": {
                "wavespeed_api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Your WaveSpeed API key"
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Text prompt describing the desired video"
                }),
                "resolution": (["480p", "720p", "1080p"], {
                    "default": "720p",
                    "tooltip": "Video resolution"
                }),
                "aspect_ratio": (["16:9", "9:16", "1:1", "4:3", "3:4"], {
                    "default": "16:9",
                    "tooltip": "Aspect ratio of the video"
                }),
                "duration": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 30,
                    "step": 1,
                    "display": "number",
                    "tooltip": "Duration of the video in seconds (max 30)"
                }),
            },
            "optional": {
                "reference_images": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "List of reference image URLs or paths (one per line)"
                }),
                "reference_videos": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "List of reference video URLs or paths (one per line)"
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "status")
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "generate_video"
    OUTPUT_NODE = True
    CATEGORY = "WaveSpeed"

    def generate_video(self, wavespeed_api_key, prompt, resolution, aspect_ratio, duration,
                       reference_images="", reference_videos=""):
        """
        Generate a video using the WaveSpeed AI API.

        Args:
            wavespeed_api_key: API key for authentication
            prompt: Text prompt for video generation
            resolution: Video resolution (480p, 720p, 1080p)
            aspect_ratio: Aspect ratio of the video
            duration: Duration in seconds (1-30)
            reference_images: Newline-separated list of reference image URLs/paths
            reference_videos: Newline-separated list of reference video URLs/paths

        Returns:
            Tuple of (video_url, status_message)
        """
        base_url = "https://api.wavespeed.ai/api/v3/bytedance/seedance-2.5-flash/reference-to-video"

        # Parse reference images and videos from newline-separated strings
        ref_images_list = [img.strip() for img in reference_images.split("\n") if img.strip()]
        ref_videos_list = [vid.strip() for vid in reference_videos.split("\n") if vid.strip()]

        # Prepare the request payload
        payload = {
            "prompt": prompt,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "duration": duration,
        }

        # Add reference images if provided
        if ref_images_list:
            payload["reference_images"] = ref_images_list

        # Add reference videos if provided
        if ref_videos_list:
            payload["reference_videos"] = ref_videos_list

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {wavespeed_api_key}"
        }

        try:
            # Make the POST request to the WaveSpeed API
            response = requests.post(
                base_url,
                headers=headers,
                json=payload,
                timeout=300  # 5 minute timeout for video generation
            )

            # Check if the request was successful
            response.raise_for_status()

            # Parse the response
            result = response.json()

            # Extract video URL from response (adjust based on actual API response structure)
            video_url = result.get("video_url", "")
            status = f"Success: Video generated successfully"

            return (video_url, status)

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {json.dumps(error_detail)}"
            except:
                error_msg += f" - {e.response.text}"
            return ("", error_msg)

        except requests.exceptions.RequestException as e:
            return ("", f"Request Error: {str(e)}")

        except Exception as e:
            return ("", f"Unexpected Error: {str(e)}")


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "WaveSpeedReferenceToVideo": WaveSpeedReferenceToVideo
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedReferenceToVideo": "WaveSpeed Reference to Video"
}
