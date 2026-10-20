#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerates audio using Vieneu from the audited and standardized voiceover.
"""
import os
import re
import json
import subprocess
import numpy as np
import soundfile as sf
from audit_voiceover import audit_and_clean_voiceover

def split_into_clean_sentences(text: str):
    text = re.sub(r'\s+', ' ', text).strip()
    raw_sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = []
    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) > 140:
            sub_parts = re.split(r'(?<=[,;:])\s+', s)
            curr = ""
            for p in sub_parts:
                if len(curr) + len(p) + 1 <= 130:
                    curr = f"{curr} {p}".strip()
                else:
                    if curr:
                        sentences.append(curr)
                    curr = p
            if curr:
                sentences.append(curr)
        else:
            sentences.append(s)
    return sentences

def main():
    cleaned_file = "video/public/audio/cleaned_voiceover_debug.txt"
    cleaned_scenes, changes = audit_and_clean_voiceover(cleaned_file)

    # Save cleaned file back
    with open(cleaned_file, "w", encoding="utf-8") as f:
        for sid, body in cleaned_scenes.items():
            f.write(f"=== {sid.upper()} ===\n{body}\n\n")
    print(f"Updated {cleaned_file} with {len(changes)} corrections.")

    out_dir = "video/public/audio"
    os.makedirs(out_dir, exist_ok=True)

    print("\nLoading Vieneu TTS model (mode=v3nano, voice=Minh Quân)...")
    from vieneu import Vieneu
    tts = Vieneu(mode="v3nano")
    voice_name = "Minh Quân"
    print("Vieneu loaded successfully.")

    durations = {}

    for scene_id in sorted(cleaned_scenes.keys()):
        body = cleaned_scenes[scene_id]
        print(f"\n==========================================")
        print(f"Generating Audio for {scene_id.upper()}")
        print(f"==========================================")

        wav_path = os.path.join(out_dir, f"{scene_id}.wav")
        mp3_path = os.path.join(out_dir, f"{scene_id}.mp3")

        sentences = split_into_clean_sentences(body)
        print(f"Total sentence chunks: {len(sentences)}")

        audio_segments = []
        sample_rate = 24000

        for idx, sentence in enumerate(sentences, 1):
            if not sentence.strip():
                continue
            try:
                seg_audio = tts.infer(sentence, voice=voice_name)
                if hasattr(seg_audio, "cpu"):
                    seg_audio = seg_audio.cpu().numpy()
                elif hasattr(seg_audio, "numpy"):
                    seg_audio = seg_audio.numpy()

                audio_segments.append(seg_audio)
                silence = np.zeros(int(sample_rate * 0.16), dtype=seg_audio.dtype)
                audio_segments.append(silence)
                print(f"  [{idx}/{len(sentences)}] ({len(sentence)} chars) OK")
            except Exception as e:
                print(f"  [{idx}/{len(sentences)}] Error: {e}")

        if not audio_segments:
            print(f"Error: No audio segments for {scene_id}!")
            continue

        full_audio = np.concatenate(audio_segments)
        sf.write(wav_path, full_audio, sample_rate)
        duration_sec = len(full_audio) / sample_rate
        print(f"Saved WAV: {wav_path} ({duration_sec:.2f}s)")

        cmd = [
            "ffmpeg", "-y", "-i", wav_path,
            "-b:a", "192k",
            "-ar", "44100",
            mp3_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        frames_30 = int(round(duration_sec * 30))
        frames_60 = int(round(duration_sec * 60))
        durations[scene_id] = {
            "duration": round(duration_sec, 3),
            "frames30": frames_30,
            "frames60": frames_60
        }
        print(f"Converted MP3: {duration_sec:.2f}s (~{frames_30} frames @ 30fps)")

    durations_file = "video/src/data/audioDurations.json"
    with open(durations_file, "w", encoding="utf-8") as f:
        json.dump(durations, f, indent=2, ensure_ascii=False)
    print(f"\nWrote durations metadata to {durations_file}")

if __name__ == "__main__":
    main()
