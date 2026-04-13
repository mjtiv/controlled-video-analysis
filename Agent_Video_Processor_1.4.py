#!/usr/bin/env python3.10

import base64
import json
import mimetypes
import cv2
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import csv


########################################
# PIPELINE OVERVIEW
#
# 1. Read the video
# 2. Extract frames at a controlled rate
# 3. Save frame metadata
# 4. Send selected frames to the AI Model
# 5. Aggregate results into a timeline/report
########################################



#########################################################################################################################
################################################## Process Images  #####################################################
#########################################################################################################################

def extract_frames(video_path: str, output_dir: str, sample_fps: float = 1.0):
    """
    Extract frames from a video at a chosen sampling rate.

    Args:
        video_path: Path to input video.
        output_dir: Directory where frames will be saved.
        sample_fps: Number of frames to save per second.

    Returns:
        A list of dictionaries with frame metadata.
    """

    # Creates the output directory for the frames
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Opens Video File and Captures Frame by Frame
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    # Defining CoreMeta Data Variables about Video
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / original_fps if original_fps > 0 else 0

    # Validate that video FPS metadata was read correctly
    if original_fps <= 0:
        raise ValueError("Could not determine video FPS.")

    # Convert the requested sampling rate (frames/sec) into a frame interval
    # Example: if original_fps = 30 and sample_fps = 1, save every 30th frame
    frame_interval = max(int(round(original_fps / sample_fps)), 1)

    metadata = []
    frame_idx = 0
    saved_idx = 0

    # Parses apart Video into Specific Images for Saving
    while True:
        success, frame = cap.read()
        if not success:
            break

        if frame_idx % frame_interval == 0:
            timestamp_sec = frame_idx / original_fps
            filename = f"frame_{saved_idx:03d}_t{timestamp_sec:.2f}.jpg"
            frame_path = output_path / filename

            cv2.imwrite(str(frame_path), frame)

            # Store traceable metadata linking saved frames back to original video time/index
            metadata.append({
                "saved_frame_index": saved_idx,
                "original_frame_index": frame_idx,
                "timestamp_sec": round(timestamp_sec, 2),
                "frame_path": str(frame_path)
            })

            saved_idx += 1

        frame_idx += 1

    # Closes the Video File
    cap.release()

    # Prints Summary Report of Analysis
    print(f"Original FPS: {original_fps:.2f}")
    print(f"Total frames: {total_frames}")
    print(f"Duration (sec): {duration_sec:.2f}")
    print(f"Saved frames: {len(metadata)}")

    return metadata


#########################################################################################################################
################################################## Process Images  #####################################################
#########################################################################################################################


def image_file_to_data_url(image_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(image_path.name)
    if mime_type is None:
        mime_type = "image/png"

    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def classify_image(client: OpenAI, image_path: Path, analysis_prompt: str) -> dict:
    image_data_url = image_file_to_data_url(image_path)

    response = client.responses.create(
        model="gpt-5.4",
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "You are an image analysis assistant. Return only strict JSON."
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": analysis_prompt,
                    },
                    {
                        "type": "input_image",
                        "image_url": image_data_url,
                    },
                ],
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "image_identification",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "target_present": {
                            "type": "boolean"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "notes": {
                            "type": "string"
                        }
                    },
                    "required": ["target_present", "confidence", "notes"],
                    "additionalProperties": False,
                },
            }
        },
    )

    data = json.loads(response.output_text)
    data["filename"] = image_path.name

    if response.usage:
        data["usage"] = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens,
        }

    return data


def analyze_images(location_images, analysis_prompt, output_json, client, results):

    """
    Loops over the folder of images and identifies if the object is present or not

    """

    # Pathway and File Name for Output
    output_json_file = location_images / output_json


    # Monitor Tokens
    total_tokens = 0
    input_tokens = 0
    output_tokens = 0

    # Loops over the images to label
    for image_path in sorted(location_images.glob("*.jpg")):
        try:
            result = classify_image(client, image_path, analysis_prompt)
            results.append(result)

            if "usage" in result:
                total_tokens  += result["usage"]["total_tokens"]
                input_tokens  += result["usage"]["input_tokens"]
                output_tokens += result["usage"]["output_tokens"]

            print(f"{image_path.name} -> present: {result['target_present']} "
                f"(conf: {result['confidence']:.2f}) | {result['notes']}")
        
        except Exception as exc:
            print(f"ERROR processing {image_path.name}: {exc}")

    output_json_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved results to: {output_json_file}")

    return total_tokens, input_tokens, output_tokens, output_json_file


def convert_results_to_csv(json_file_path: Path, output_dir: Path):
    """
    Converts analysis JSON results into a CSV file for Excel-friendly sorting.
    """

    # Load JSON
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Output CSV path
    output_csv = output_dir / "analysis_results_table.csv"

    # Define columns
    fieldnames = [
        "filename",
        "timestamp_sec",
        "target_present",
        "target_present_int",
        "confidence",
        "notes",
        "input_tokens",
        "output_tokens",
        "total_tokens"
    ]

    rows = []

    for item in data:
        filename = item.get("filename", "")

        # Extract timestamp from filename (frame_000_t0.00.jpg)
        try:
            timestamp = float(filename.split("_t")[1].replace(".jpg", ""))
        except Exception:
            timestamp = None

        usage = item.get("usage", {})

        row = {
            "filename": filename,
            "timestamp_sec": timestamp,
            "target_present": item.get("target_present"),
            "target_present_int": int(item.get("target_present", False)),
            "confidence": item.get("confidence"),
            "notes": item.get("notes"),
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }

        rows.append(row)

    # Write CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV saved to: {output_csv}")

#########################################################################################################################
############################################ Main Function ##############################################################
#########################################################################################################################

def main():

    ################################Parameters#############################
    
    # Input Video File
    video_file = Path(r"D:\Coding_Agents\Controlled_Agent_Loop_Video\green_car_video_clip.mp4")

    # Directory for Frames
    frames_dir = "frames"

    # Number of frames to sample per second of video
    sample_fps=1.0

    # Identification Variable for AI Prompt
    analysis_prompt = "Determine whether a bright green sedan is present in this frame."


    # Output File Name (will be placed with images)
    output_json = "analysis_results.json"

    # Estimated token costs (03/21/2025)
    INPUT_COST_PER_TOKEN = 0.0000025
    OUTPUT_COST_PER_TOKEN = 0.000015


    #######################################################################
    # FPS References Table
    #
    # FPS Where you see it    Feel
    # 24 fps  Movies / cinema “film look”
    # 25 fps  Europe broadcast    standard TV (PAL)
    # 29.97 / 30 fps  US video / phones / web most common (Grok videos)
    # 60 fps  sports / gaming / newer phones  very smooth
    # 120 fps+    slow motion ultra smooth
    #######################################################################


    print ("\n")
    print ("Starting Program")
    print ("\n")

    frame_metadata = extract_frames(video_file, frames_dir, sample_fps)
    for item in frame_metadata:
        print(item)

    # Location of Images
    frames_dir = Path("frames")
    location_images = frames_dir


    # Calling the API client
    load_dotenv()
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY:
        raise ValueError("OPENAI_API_KEY not found")
    client = OpenAI(api_key=API_KEY)
    
    # List to Store Results
    results = []

    print ("Starting to Analyze Images")
    # Calls the main analysis function
    total_tokens, input_tokens, output_tokens, output_json_file = analyze_images(location_images, analysis_prompt, output_json, client, results)
    print ("Done Analyzing Images")

    num_images = len(results)
    avg_tokens = total_tokens / num_images if num_images else 0
    input_cost  = input_tokens * INPUT_COST_PER_TOKEN
    output_cost = output_tokens * OUTPUT_COST_PER_TOKEN
    total_cost  = input_cost + output_cost

    print("\n--- Run Summary ---")
    print(f"Images processed: {num_images}")
    print(f"Total tokens: {total_tokens}")
    print(f"Input tokens: {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Avg tokens/image: {avg_tokens:.2f}")
    print(f"Input cost:  ${input_cost:.4f}")
    print(f"Output cost: ${output_cost:.4f}")
    print(f"Total cost:  ${total_cost:.4f}")
    print ("\n")
    print ("\n")

    print ("Converting Final Results to CSV File")
    #output_json_file=Path(r"D:\Coding_Agents\Controlled_Agent_Loop_Video\frames\analysis_results.json")
    # Convert Analysis into an Excel File For Easier Sorting
    convert_results_to_csv(output_json_file, location_images)
    print ("Done Conversion")

    print ("\n")
    print ("\n")
    print ("Done Running Program")


          
if __name__ == "__main__":
    main()   












