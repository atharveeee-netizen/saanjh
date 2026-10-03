# SAANJH Blender Visualization

This directory contains the Python script to procedurally generate a 3D visualization of the SAANJH flexibility event using Blender.

## Prerequisites
- Blender 3.6 or higher installed on your desktop.

## How to Render the Event
1. Open Blender.
2. Delete the default cube, camera, and light (Press `A` then `X`).
3. Switch to the **Scripting** workspace (top tab).
4. Click **New** to create a new text block.
5. Open `blender/scripts/animate_event.py` from this repository and copy its entire contents into the Blender text editor.
6. Press the **Run Script** button (the play icon ⏯️) in the text editor header.

## What it Does
The script procedurally generates:
* A 60-home Indian neighbourhood layout.
* A central Distribution Transformer.
* Glowing energy lines connecting homes to the transformer.
* A 90-frame animation showing the "Intermittency Gap" (sunset, lights turn on, transformer glows red).
* The SAANJH Intervention (green flexibility waves pulse from homes, transformer cools down).

## Output
You can render the animation to a video file:
1. Go to Output Properties in Blender.
2. Set File Format to `FFmpeg video`.
3. Press `Ctrl + F12` to render the animation. Use this video in your hackathon pitch!
