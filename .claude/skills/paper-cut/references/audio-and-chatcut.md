# Audio and ChatCut handoff

## Narration is timing truth

Generate or import one approved clean master track, then obtain word-level timestamps before locking scenes, captions, SFX, and camera cues. Audition a short voice sample before a paid full take.

## Shortening approved narration

When the user deletes a passage:

1. locate the first and last deleted spoken words from transcription;
2. cut only that interval from a derivative audio file;
3. add a short crossfade at the join and audition it;
4. preserve the approved voice instead of regenerating it;
5. subtract the exact removed duration from every downstream scene, SFX, text cue, camera move, assertion, and total duration;
6. recheck transitions and the final hold.

## Captions and key text

Keep captions as structured timestamp data, never baked into scene images. Hero wordmarks are not subtitles: use them selectively and keep normal labels editable.

## ChatCut optional path

Use ChatCut when the user wants a specific Chinese voice, transcription, subtitle correction, generated SFX/music, an editable finishing timeline, or ChatCut export. Load the relevant ChatCut skills and keep the HyperFrames project as the animation master.

Do not rebuild the collage as ChatCut AI video generation. A hybrid requires explicit approval and separate labeling of generated video inserts.
