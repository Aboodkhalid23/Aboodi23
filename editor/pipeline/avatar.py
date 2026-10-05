"""The owner as a drawn character inside the story (owner's idea): only his FACE is taken, a character of him is
designed once per look (cartoon, paper cut-out, anime, sketch, comic, clay), saved on Higgsfield as a reference
"Element", and every `avatar` beat draws the story's scene with him in it doing what the script says (fixing the
machines in the factory, running from the bank…). Then it moves: the code animates the drawing in layers (he
breathes, settles in, the scene drifts behind him) or, for the big moments (`"animate": "ai"`), a video model
moves the drawing itself.

Steps (Claude does the generating with the Higgsfield tools; nothing is spent without the owner's credit budget):
  1. `face-ref`         clear head crops from the episode → assets/face_ref_*.jpg
  2. `character-jobs`   for each look the plan uses that has no character yet → work/character_jobs.json
                        (generate the design from the face crops, create an Element from it, then
                        `avatar-register --look <look> --element <id>`)
  3. `ai-jobs`          scene prompts with the character's element inside → work/ai_jobs.json
  4. `ai-fetch --part fg` (optional) the character cut out of the scene (Higgsfield remove_background) for the
                        layered motion; without it the code finds him itself.
The character ids live in editor/characters.json (ids only: no pictures of him in the public repo)."""
import json
from datetime import date
from pathlib import Path

from .paths import Episode

CHARACTERS = Path(__file__).resolve().parent.parent / "characters.json"
IMAGE_MODEL = "nano_banana_pro"      # keeps a reference Element's face across scenes; 16:9; up to 4k
VIDEO_MODEL = "seedance_2_0_mini"    # budget image-to-video that keeps the identity (start_image + element)
LOOKS = {
    "cartoon": "3D animated feature-film cartoon style, expressive caricature proportions, soft studio lighting, "
               "rich colours, Pixar-like rendering",
    "paper": "handmade paper cut-out collage style, layered craft paper with visible fibres and scissor-cut edges, "
             "flat colours, soft drop shadows between layers, documentary collage",
    "anime": "Japanese anime film style, clean line art, cel shading, painted backgrounds, cinematic anime lighting",
    "sketch": "hand-drawn pencil and ink illustration on cream paper, cross-hatching, sketchbook documentary drawing",
    "comic": "bold graphic-novel illustration, thick ink outlines, halftone dots, dramatic flat colours",
    "clay": "claymation stop-motion style, plasticine textures with fingerprints, miniature handmade set",
}


def load_characters() -> dict:
    return json.loads(CHARACTERS.read_text(encoding="utf-8")) if CHARACTERS.exists() else {"looks": {}}


def register(look: str, element_id: str, note: str = "") -> dict:
    if look not in LOOKS:
        raise ValueError(f"الشكل لازم من {', '.join(LOOKS)}")
    d = load_characters()
    d.setdefault("looks", {})[look] = {"element_id": element_id, "model": IMAGE_MODEL, "made": date.today().isoformat(),
                                       **({"note": note} if note else {})}
    CHARACTERS.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return d


def element(look: str) -> str | None:
    return (load_characters().get("looks", {}).get(look) or {}).get("element_id")


def design_prompt(look: str) -> str:
    return (f"Character design of the man in the reference photos, as a {LOOKS[look]}. Keep his real identity "
            "recognisable: same face shape, eyes, nose, beard and hairstyle. Full body, standing, relaxed neutral pose, "
            "casual dark sweater, facing three-quarters to the camera, plain light grey background, no text.")


def scene_prompt(look: str, scene: str, element_id: str) -> str:
    return (f"{LOOKS[look]}. {scene.rstrip('. ')}. The main character is <<<{element_id}>>> — the same character, same "
            "face and style. Wide 16:9 cinematic composition, the character clearly visible and about a third of the "
            "frame tall, expressive pose and face that act out the moment, a detailed background that tells where we "
            "are, no text, no captions.")


def character_jobs(ep: Episode, looks: list[str]) -> list[dict]:
    """Looks the plan needs that have no saved character yet: what to generate, from which face crops."""
    refs = sorted(str(p) for p in ep.assets.glob("face_ref_*.jpg"))
    jobs = [{"look": look, "model": IMAGE_MODEL, "aspect_ratio": "3:4", "prompt": design_prompt(look),
             "face_refs": refs, "then": f"manage_reference_elements create (category character, name abood-{look}) "
                                        f"from the image job; then: python -m editor.pipeline avatar-register "
                                        f"{ep.root} --look {look} --element <element id>"}
            for look in dict.fromkeys(looks) if not element(look)]
    (ep.work / "character_jobs.json").write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
    return jobs
