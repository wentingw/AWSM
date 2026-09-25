"""Build the frozen M4 drone query/replay comparison panel."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, shutil, cv2, os, subprocess

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / 'experiments/tasks/drone_M4/replay_20260924'
REF = ROOT / 'experiments/tasks/frozen_inputs/photographic_mapping_queries'
PANEL_OUT = ROOT / 'figures/m4_tasks'
OUT = ROOT / 'blog/assets/m4_tasks'
PANEL_OUT.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
REPORT = ROOT / 'results/evaluation/tasks/drone_M4_20260924/report.json'

IDS = [0, 3, 13]
W, H = 640, 360
PAD, LABEL = 18, 34

def font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def fit(path):
    im = Image.open(path).convert('RGB'); im.thumbnail((W, H))
    canvas = Image.new('RGB', (W, H), '#e8eceb')
    canvas.paste(im, ((W-im.width)//2, (H-im.height)//2)); return canvas

def main():
    report = json.loads(REPORT.read_text())
    byid = {x['query_id']: x for x in report['episodes']}
    rows=[]
    for q in IDS:
        ep = REPLAY / f'episode_{q:02d}'
        ref = REF / f'reference_{q:02d}.png'
        if not ref.exists(): raise FileNotFoundError(ref)
        a = byid[q]
        rows.append((q, fit(ref), fit(ep/'final_rgb.png'), a))
    top_h = 46
    header_h, footer_h, gap = 38, 30, 14
    row_h = header_h + H + footer_h + gap
    panel = Image.new('RGB', (PAD + 2*W + PAD, top_h + len(rows)*row_h + PAD), 'white')
    draw = ImageDraw.Draw(panel); title=font(22); small=font(18); tiny=font(15)
    draw.text((PAD, 8), 'M4 drone reference-image search and rephotography', fill='#16222a', font=title)
    y=top_h + header_h
    for q, ref, achieved, a in rows:
        draw.text((PAD, y-header_h+8), f'Query {q}', fill='#16222a', font=small)
        panel.paste(ref, (PAD, y)); panel.paste(achieved, (PAD+W, y))
        draw.text((PAD+8, y+8), 'reference', fill='white', stroke_width=2, stroke_fill='#111')
        draw.text((PAD+W+8, y+8), 'achieved endpoint', fill='white', stroke_width=2, stroke_fill='#111')
        status = 'collision' if a['flight_status']=='collision' else 'collision-free'
        draw.text((PAD, y+H+7), f"{status}; Δt {a['translation_error_m']:.3f} m; ΔR {a['rotation_error_deg']:.2f}°; PSNR {a['psnr_db']:.2f} dB; SSIM {a['ssim']:.3f}", fill='#33434d', font=tiny)
        y += row_h
    panel.save(PANEL_OUT/'drone_comparison.jpg', quality=92, optimize=True)
    print(str(OUT))

if __name__ == '__main__': main()
