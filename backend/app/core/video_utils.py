import cv2
import base64
import logging

logger = logging.getLogger(__name__)

def extract_keyframes(video_path: str, num_frames: int = 3) -> list[str]:
    """
    Extracts evenly spaced keyframes from a video file and returns them as Base64 encoded JPEG strings.
    Resizes the frames to a maximum dimension to optimize for Vision LLM token usage.
    """
    logger.info(f"Extracting {num_frames} keyframes from {video_path}")
    frames_base64 = []
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Failed to open video file: {video_path}")
        return frames_base64

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames <= 0:
        logger.error("Could not determine total frames.")
        cap.release()
        return frames_base64

    # Calculate frame indices to extract, avoiding the very beginning and very end (often black screens or logos)
    step = max(1, total_frames // (num_frames + 1))
    frame_indices = [step * i for i in range(1, num_frames + 1)]

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Resize frame to save token cost on OpenAI Vision API (e.g. 512px max dimension)
            # Vision APIs process images more efficiently when they aren't massive.
            height, width = frame.shape[:2]
            max_dim = 512
            if width > max_dim or height > max_dim:
                scale = max_dim / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))

            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            # Encode JPEG to Base64 string
            b64_str = base64.b64encode(buffer).decode('utf-8')
            # Prefix it so the OpenAI API recognizes the format natively
            b64_data_uri = f"data:image/jpeg;base64,{b64_str}"
            frames_base64.append(b64_data_uri)
        else:
            logger.warning(f"Failed to read frame at index {idx}")

    cap.release()
    logger.info(f"Successfully extracted {len(frames_base64)} frames.")
    return frames_base64
