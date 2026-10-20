import os
import re
import sys
import json
import subprocess
import numpy as np
import soundfile as sf

def split_into_sentences(text: str):
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Split by sentence end markers (. ! ?)
    raw_sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = []
    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        # If sentence is too long (> 160 chars), split by comma or colon
        if len(s) > 160:
            sub_parts = re.split(r'(?<=[,;:])\s+', s)
            curr = ""
            for p in sub_parts:
                if len(curr) + len(p) + 1 <= 150:
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

def parse_voiceover_script(script_path: str):
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = re.split(r"## PHẦN (\d+):", content)
    scenes = {}
    for i in range(1, len(sections), 2):
        sec_num = int(sections[i])
        sec_text = sections[i+1].strip()
        # The body is everything after the title line
        lines = sec_text.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        scenes[f"scene{sec_num}"] = {
            "num": sec_num,
            "title": title,
            "body": body
        }
    return scenes

def main():
    script_path = "video/voiceover-script.md"
    out_dir = "video/public/audio"
    os.makedirs(out_dir, exist_ok=True)

    print("Parsing voiceover script...")
    scenes = parse_voiceover_script(script_path)
    print(f"Loaded {len(scenes)} scenes.")

    print("\nLoading Vieneu TTS model (mode=v3nano, voice=Minh Quân)...")
    from vieneu import Vieneu
    tts = Vieneu(mode="v3nano")
    voice_name = "Minh Quân"
    print("Vieneu loaded successfully on device.")

    durations = {}

    for scene_id, data in scenes.items():
        print(f"\n==========================================")
        print(f"Generating Audio for {scene_id.upper()}: {data['title']}")
        print(f"==========================================")

        wav_path = os.path.join(out_dir, f"{scene_id}.wav")
        mp3_path = os.path.join(out_dir, f"{scene_id}.mp3")

        sentences = split_into_sentences(data["body"])
        print(f"Total sentence chunks: {len(sentences)}")

        audio_segments = []
        sample_rate = 24000

        for idx, sentence in enumerate(sentences, 1):
            if not sentence.strip():
                continue
            try:
                # Infer with Vieneu
                seg_audio = tts.infer(sentence, voice=voice_name)
                # seg_audio is numpy array or tensor
                if hasattr(seg_audio, "cpu"):
                    seg_audio = seg_audio.cpu().numpy()
                elif hasattr(seg_audio, "numpy"):
                    seg_audio = seg_audio.numpy()
                
                audio_segments.append(seg_audio)
                # Add 0.2s silence between sentences
                silence = np.zeros(int(sample_rate * 0.2), dtype=np.float32)
                audio_segments.append(silence)
                print(f"  [{idx}/{len(sentences)}] ({len(sentence)} chars) OK")
            except Exception as e:
                print(f"  [{idx}/{len(sentences)}] ERROR on '{sentence[:30]}...': {e}")

        if not audio_segments:
            print(f"WARNING: No audio generated for {scene_id}!")
            continue

        full_audio = np.concatenate(audio_segments)
        sf.write(wav_path, full_audio, sample_rate)
        print(f"Saved WAV: {wav_path} ({len(full_audio)/sample_rate:.2f}s)")

        # Convert to MP3
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_path,
            "-b:a", "192k", mp3_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Probe duration
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", mp3_path
        ], stdout=subprocess.PIPE, text=True, check=True)
        dur = float(res.stdout.strip())
        frames_30 = int(dur * 30)
        frames_60 = int(dur * 60)
        durations[scene_id] = {
            "duration": dur,
            "frames30": frames_30,
            "frames60": frames_60,
            "title": data["title"]
        }
        print(f"Converted MP3: {dur:.2f}s (~{frames_30} frames @ 30fps, ~{frames_60} frames @ 60fps)")

    # Save durations JSON
    json_path = "video/src/data/audioDurations.json"
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(durations, f, ensure_ascii=False, indent=2)
    print(f"\nWrote durations metadata to {json_path}")
    print("ALL SCENES COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
