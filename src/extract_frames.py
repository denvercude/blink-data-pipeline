import os
from pathlib import Path
from datetime import datetime
import cv2

# BASE_DIR = src/
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_CLIPS_DIR = DATA_DIR / "raw_clips"
FRAMES_ROOT = DATA_DIR / "frames"  # we’ll put camera/date under here


def parse_date_from_filename(filename: str) -> str:
    """
    Try to extract a date from a Blink-style filename.
    Adjust this to match your actual filenames if needed.

    Examples we try:
      2025-11-20_09-10-11.mp4
      clip_2025-11-20_09-10-11.mp4

    Returns a date string 'YYYY-MM-DD'. If parsing fails, returns 'unknown_date'.
    """
    name, _ = os.path.splitext(filename)

    # Grab the last 19 chars if they look like a datetime: 'YYYY-MM-DD_HH-MM-SS'
    # e.g. '2025-11-20_09-10-11'
    for part in name.split("_"):
        try:
            dt = datetime.strptime(part, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Try pattern 'YYYY-MM-DD_HH-MM-SS'
    try:
        dt = datetime.strptime(name[-19:], "%Y-%m-%d_%H-%M-%S")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    print(f"  WARNING: Could not parse date from filename '{filename}'. "
          f"Placing frames under 'unknown_date'.")
    return "unknown_date"


def extract_frames_from_folder(
    input_folder: Path,
    output_root: Path,
    camera_name: str = "sort_C15",
    interval_seconds: int = 1,
    expected_width: int = 1920,
    expected_height: int = 1080,
):
    """
    Extract 1 frame per second from each .mp4 or .mov video in input_folder.
    Save frames in:
        output_root / camera_name / <date> / <camera_prefix>_XXXXXX.jpg

    Only processes videos that match the expected resolution.
    """
    valid_exts = (".mp4", ".mov")
    video_files = sorted(
        [f for f in os.listdir(input_folder) if f.lower().endswith(valid_exts)]
    )

    if not video_files:
        print(f"No video clips found in {input_folder}.")
        return

    print(f"Found {len(video_files)} video clips in {input_folder}\n")

    counter = 1  # increments across all frames for this camera

    for video_file in video_files:
        video_path = input_folder / video_file
        print(f"Processing: {video_file}")

        date_str = parse_date_from_filename(video_file)  # e.g. '2025-11-20'
        output_folder = output_root / camera_name / date_str
        output_folder.mkdir(parents=True, exist_ok=True)

        video = cv2.VideoCapture(str(video_path))
        if not video.isOpened():
            print(f"  Could not open {video_file}. Skipping.")
            continue

        fps = video.get(cv2.CAP_PROP_FPS)
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        print(f"  FPS: {fps:.2f}, Duration: {duration:.2f}s, "
              f"Resolution: {width}x{height}")

        # Adjust expected_width/height to match your Blink videos
        if width != expected_width or height != expected_height:
            print(f"  Skipping {video_file}: resolution mismatch ({width}x{height}).\n")
            video.release()
            continue

        frame_interval = int(fps * interval_seconds)
        frame_idx = 0
        saved_count = 0

        while True:
            ret, frame = video.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                filename = output_folder / f"c15_{counter:06d}.jpg"
                cv2.imwrite(str(filename), frame)
                print(f"    Saved: {filename}")
                counter += 1
                saved_count += 1

            frame_idx += 1

        video.release()
        print(f"  Extracted {saved_count} frames from {video_file}\n")

    print(f"Done! Extracted {counter - 1} frames total.")
    print(f"All frames saved under: {output_root / camera_name}")


if __name__ == "__main__":
    input_dir = RAW_CLIPS_DIR
    output_root = FRAMES_ROOT
    extract_frames_from_folder(
        input_folder=input_dir,
        output_root=output_root,
        camera_name="sort_C15",
        interval_seconds=1,
        expected_width=1920,   # tweak if your clips aren’t 1920x1080
        expected_height=1080,
    )