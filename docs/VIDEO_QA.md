# Video Generation QA

## Pipeline Overview
The video generation pipeline successfully converts the SAANJH Python simulation JSON artifacts into a data-driven 3D animation, then multiplexes the frames using `ffmpeg` into a compressed MP4 suitable for presentations.

## File Hierarchy
- `artifacts/video/frames/` - Raw JPEG output directory from Blender
- `compile_video.py` - Custom concatenator for handling non-sequential frames during previews.
- `saanjh_digital_twin_preview.mp4` - Rapidly compiled timeline verification of the event (10fps).
- `VOICEOVER_SCRIPT.md` / `VOICEOVER_SUBTITLES.srt` - Timing-aligned scripts for demonstration overlay.

## Story Alignment
The final video tracks precisely with the requested narrative arc:
1. **Normal Operation:** Clock and simulation initialize. No active stress.
2. **Forecast Warning:** The UI highlights "FORECAST WARNING" before physical strain hits the transformer.
3. **Dispatch:** The Virtual Battery aggressively glows to represent flexibility delivered. 
4. **Relief & Recovery:** Feeder glow and transformer stress visibly drop, mapping perfectly to the underlying numerical flexibility extraction logic.

## Validation Pass
- [x] Does the visualization contain an operational UI HUD?
- [x] Is the frame populated by an industrial neighbourhood structure (not a flat plane)?
- [x] Are the actual metrics from `saanjh_visualization_data.json` visually updating on the UI panels frame-by-frame?
- [x] Are battery dispatches linked mathematically to the SAANJH flexibility values?
- [x] Is a professional video file exported without requiring manual compositing?

**STATUS:** All video QA checks passed.
