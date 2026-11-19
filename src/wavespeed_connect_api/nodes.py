from inspect import cleandoc
import requests
import json
import time
import math
from server import PromptServer


class WaveSpeedReferenceToVideo:
    """
    A ComfyUI node that connects to the WaveSpeed AI API for reference-to-video generation.
    Uses the Seedance 2.5 Flash model to generate videos from reference images and videos.
    Polls for the result after submitting the task.
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

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_url",)
    OUTPUT_NODE = True
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "generate_video"
    CATEGORY = "WaveSpeed"

    def poll_for_result(self, task_id, api_key, max_attempts=60, poll_interval=5):
        """
        Poll the WaveSpeed API for the result of a video generation task.

        Args:
            task_id: The task ID returned from the initial request
            api_key: The API key for authentication
            max_attempts: Maximum number of polling attempts (default: 60)
            poll_interval: Seconds between polling attempts (default: 5)

        Returns:
            Tuple of (video_url, status_message, ui_updates)
        """
        result_url = f"https://api.wavespeed.ai/api/v3/predictions/{task_id}/result"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        ui_updates = []

        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    result_url,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()

                # Check the status field in the response
                status = result["data"].get("status", "unknown")
                status_msg = f"Status: {status} / {math.ceil(((attempt + 1) / 60) * 100) }%"
                print("polling: sending an update for generation")
                PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                    "message": status_msg
                })
                ui_updates.append(status_msg)

                if status == "completed":
                    # Video generation is complete, extract the video URL
                    video_url = result["data"].get("outputs", None)
                    if not video_url:
                        video_url = video_url[0]
                    final_status = f"Completed after {attempt + 1} polling attempts"
                    print("polling: video gen success")
                    PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                        "message": final_status
                    })
                    ui_updates.append(final_status)
                    return (video_url, final_status, ui_updates)

                elif status == "failed":
                    # Video generation failed
                    final_status = f"Video Generation failed. This error was due to Wavespeed servers"
                    print("polling: video gen failed")
                    PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                        "message": final_status
                    })
                    ui_updates.append(final_status)
                    return ("", final_status, ui_updates)

                elif status in ("processing", "queued", "pending"):
                    # Task is still in progress, continue polling
                    print("polling: video gen still in processing")
                    time.sleep(poll_interval)
                    continue

                else:
                    # Unknown status, continue polling
                    time.sleep(poll_interval)
                    continue

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # Task not found or not ready yet, continue polling
                    status_msg = f"Task not ready yet (404)"
                    print("polling: sending http error")
                    PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                        "message": status_msg
                    })
                    ui_updates.append(status_msg)
                    time.sleep(poll_interval)
                    continue
                error_msg = f"HTTP Error during polling: {e.response.status_code}"
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {json.dumps(error_detail)}"
                except:
                    error_msg += f" - {e.response.text}"
                print("polling: sending http error other than 404")
                PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                    "message": error_msg
                })
                ui_updates.append(error_msg)
                return ("", error_msg, ui_updates)

            except requests.exceptions.RequestException as e:
                error_msg = f"Request Error during polling: {str(e)}"
                print("polling: requests lib error")
                PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                    "message": error_msg
                })
                ui_updates.append(error_msg)
                return ("", error_msg, ui_updates)

            except Exception as e:
                error_msg = f"Unexpected Error during polling: {str(e)}"
                print("polling: unexpected error")
                PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                    "message": error_msg
                })
                ui_updates.append(error_msg)
                return ("", error_msg, ui_updates)

        # Max attempts reached
        timeout_msg = f"Timeout: Task did not complete after {max_attempts} polling attempts"
        print("polling: max timeout")
        ui_updates.append(timeout_msg)
        return ("", timeout_msg, ui_updates)

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
            UI output for display on the canvas
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
                timeout=60
            )

            # Check if the request was successful
            response.raise_for_status()

            # Parse the response
            result = response.json()
            print(f"the result from the response: {result}")
            print(f"data is {result["data"]}")
            # Extract task_id from response
            task_id = result["data"].get("id", None)

            if not task_id:
                print("Task id was not returned from API")
                error_text = f"Error: No task_id returned from API. Response: {json.dumps(result)}"
                PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                    "message": error_text
                })
                return ""

            # Poll for the result
            video_url, poll_status, ui_updates = self.poll_for_result(task_id, wavespeed_api_key)

            status_message = f"Task ID: {task_id} | {poll_status}"
            print("sending task id and poll status")
            PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                "message": status_message
            })
            # Combine all UI messages
            all_messages = ui_updates + [status_message]
            if video_url:
                all_messages.append(f"Video URL: {video_url}")
                print("got the video url")
                PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                    "message": "Video rendered!"
                })
                return video_url
            
            print("saying that the video gen failed")
            PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                "message": "Video Generation failed!"
            })
            return ""

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {json.dumps(error_detail)}"
            except:
                error_msg += f" - {e.response.text}"
            print("sending http error")
            PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                "message": error_msg
            })
            return ""

        except requests.exceptions.RequestException as e:
            error_msg = f"Request Error: {str(e)}"
            print("sending error from requests library")
            PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                "message": error_msg
            })
            return ""
            

        except Exception as e:
            error_msg = f"Unexpected Error: {str(e)}"
            print("sending an exception")
            PromptServer.instance.send_sync("wavespeed.wavespeedreftovideo.update_status", {
                "message": error_msg
            })
            return ""
            

# A dictionary that contains all all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "WaveSpeedReferenceToVideo": WaveSpeedReferenceToVideo
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedReferenceToVideo": "WaveSpeed Reference to Video"
}
