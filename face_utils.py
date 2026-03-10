from deepface import DeepFace
import numpy as np

MODEL = "ArcFace"
DETECTOR = "opencv"
THRESHOLD = 0.6


def get_embedding(image_path):

    result = DeepFace.represent(
        img_path=image_path,
        model_name=MODEL,
        detector_backend=DETECTOR,
        enforce_detection=False
    )

    return np.array(result[0]["embedding"])


def compare_embeddings(stored_embedding, live_embedding):

    stored_embedding = np.array(stored_embedding)
    live_embedding = np.array(live_embedding)

    similarity = np.dot(stored_embedding, live_embedding) / (
        np.linalg.norm(stored_embedding) * np.linalg.norm(live_embedding)
    )

    print("Similarity:", similarity)

    return similarity > THRESHOLD