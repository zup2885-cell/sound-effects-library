#!/usr/bin/env python3
"""Build the 音效库 static site into ./docs from the release zip's extracted files (SRC dir)."""
import json, os, re, subprocess, sys, zipfile, struct
SRC = sys.argv[1] if len(sys.argv) > 1 else 'build/src'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'docs'
ZIP_URL = 'https://github.com/zup2885-cell/sound-effects-library/releases/download/v1.0.0/short-film-transition-sfx-pack.zip'
if not os.path.isdir(SRC) or not os.listdir(SRC):
    # Fetch the release pack and extract it flat; names are UTF-8 stored without the UTF-8 flag.
    import urllib.request
    os.makedirs(SRC, exist_ok=True); zp = os.path.join(os.path.dirname(SRC) or '.', 'pack.zip')
    if not os.path.exists(zp): urllib.request.urlretrieve(ZIP_URL, zp)
    with zipfile.ZipFile(zp) as z:
        for i in z.infolist():
            n = i.filename
            if '__MACOSX' in n or n.endswith('/'): continue
            if not i.flag_bits & 0x800:
                try: n = n.encode('cp437').decode('utf-8')
                except UnicodeError: pass
            open(os.path.join(SRC, os.path.basename(n)), 'wb').write(z.read(i))
for d in ('audio/mp3', 'audio/wav', 'zips'):
    os.makedirs(f'{OUT}/{d}', exist_ok=True)

CATS = [  # (id, 中文名, matcher) — first match wins
    ('fire',   '燃烧火焰', r'burn|fire|lighter|sizzle|crackle'),
    ('flash',  '闪光',     r'flash'),
    ('rise',   '上升蓄力', r'rise'),
    ('glitch', 'VHS/故障', r'vhs|glitch|radiation|noise'),
    ('atmos',  '氛围环境', r'atmosphere'),
    ('steps',  '脚步/自然', r'footsteps|ice crack'),
    ('retro',  '相机/复古设备', r'cam|click|polaroid|projector|phone|vinyl|radio'),
    ('paper',  '纸张/滑动', r'paper|slide'),
    ('trans',  '旋转/缩放转场', r'spin|zoom'),
    ('whoosh', '嗖声', r'whoosh'),
]
ZH = {'whoosh':'嗖','backward':'倒放','reverse':'反向','big':'大','wave':'波浪','bird':'鸟','birds':'鸟群','flapping':'扑翅',
 'camera':'相机','flash':'闪光','deep':'低沉','long':'长','sub':'超低频','distant':'远处','dream':'梦幻','catcher':'捕手',
 'drop':'下坠','explosion':'爆炸','endless':'无尽','high':'高音','fire':'火焰','light':'轻','heavy':'重','lighter':'打火机',
 'footsteps':'脚步','forest':'森林','wood':'木头','dirt':'泥土','slow':'慢动作','motion':'','snow':'雪地','ice':'冰面','wooden':'木',
 'bridge':'桥','gravel':'碎石','small':'小','beach':'海滩','glitch':'故障','hard':'硬','rock':'岩石','crack':'裂开','lake':'湖',
 'plant':'植物','stutter':'卡顿','timelapse':'延时','rise':'上升','torpedo':'鱼雷','train':'火车','tree':'树','trees':'树林',
 'wind':'风','zip':'拉链','burn':'燃烧','combo':'组合','cam':'相机','city':'城市','atmosphere':'氛围','clothes':'衣服',
 'crackle':'噼啪','factory':'工厂','noise':'噪声','outdoor':'户外','paper':'纸张','phone':'电话','polaroid':'拍立得',
 'projector':'投影机','radiation':'辐射','radio':'收音机','rain':'雨','server':'服务器','room':'机房','short':'短','simple':'简单',
 'sizzle':'滋滋','slide':'滑动','slow-mo':'慢动作','spin':'旋转','tension':'紧张','tention':'紧张','vhs':'VHS录像带','vinyl':'黑胶唱片',
 'windy':'大风','zoom':'缩放','analog':'模拟','click':'快门','in':'','on':'','the':'','a':'','at':'','with':'','of':''}

def probe(f):
    j = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
        'stream=codec_name,sample_rate,channels:format=duration','-of','json',f]))
    s = j['streams'][0]; return s['codec_name'], int(s['sample_rate']), s['channels'], float(j['format']['duration'])

def peaks(f, n=64):
    raw = subprocess.check_output(['ffmpeg','-v','error','-i',f,'-ac','1','-ar','8000','-f','s16le','-'])
    a = struct.unpack(f'<{len(raw)//2}h', raw); step = max(1, len(a)//n)
    p = [max((abs(x) for x in a[i*step:(i+1)*step]), default=0) for i in range(n)]
    m = max(p) or 1; return [round(x/m*100) for x in p]

def slug(name):
    s = re.sub(r'[（(]\s*(\d+)\s*[）)]', r'-alt\1', name)
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

items = []
natural = lambda s: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s.lower())]
for fn in sorted(os.listdir(SRC), key=natural):
    src = os.path.join(SRC, fn); base = os.path.splitext(fn)[0]
    codec, sr, ch, dur = probe(src)
    cat = next(c for c in CATS if re.search(c[2], base.lower()) or c[0]=='whoosh')
    sl = slug(base); mp3 = f'audio/mp3/{sl}.mp3'; wav = f'audio/wav/{sl}.wav'
    osr = sr if sr in (44100, 48000) else 48000
    if not os.path.exists(f'{OUT}/{mp3}'):
        subprocess.check_call(['ffmpeg','-v','error','-y','-i',src,'-ar',str(osr),'-c:a','libmp3lame','-b:a','320k','-map_metadata','-1',f'{OUT}/{mp3}'])
    if not os.path.exists(f'{OUT}/{wav}'):
        wcodec = codec if codec in ('pcm_s16le','pcm_s24le') else ('pcm_s24le' if codec.startswith('pcm') else 'pcm_s16le')
        subprocess.check_call(['ffmpeg','-v','error','-y','-i',src,'-ar',str(osr),'-c:a',wcodec,'-map_metadata','-1',f'{OUT}/{wav}'])
    words = re.findall(r'[a-z\-]+', base.lower())
    zh = ''.join(ZH.get(w, '') for w in words) or cat[1]
    num = ' '.join(re.findall(r'\d+', base))
    items.append(dict(id=sl, name=base, zh=(zh + (' ' + num if num else '')).strip(), cat=cat[0], dur=round(dur, 2),
        sr=osr, bits=24 if 's24' in (codec if codec in ('pcm_s16le','pcm_s24le') else ('pcm_s24le' if codec.startswith('pcm') else 'x')) else 16,
        orig=fn, mp3=mp3, wav=wav, mp3Size=os.path.getsize(f'{OUT}/{mp3}'), wavSize=os.path.getsize(f'{OUT}/{wav}'), peaks=peaks(src)))
    print(cat[0], base, '->', items[-1]['zh'], flush=True)

cats = []
for cid, cname, _ in CATS:
    its = [i for i in items if i['cat'] == cid]
    if not its: continue
    z = f'zips/{cid}-mp3.zip'
    with zipfile.ZipFile(f'{OUT}/{z}', 'w', zipfile.ZIP_STORED) as zf:
        for i in its: zf.write(f"{OUT}/{i['mp3']}", f"{cname.replace('/', '-')}/{i['name']}.mp3")
    cats.append(dict(id=cid, name=cname, count=len(its), zip=z, zipSize=os.path.getsize(f'{OUT}/{z}')))
with zipfile.ZipFile(f'{OUT}/zips/all-mp3.zip', 'w', zipfile.ZIP_STORED) as zf:
    for i in items:
        cn = next(c['name'] for c in cats if c['id'] == i['cat']).replace('/', '-')
        zf.write(f"{OUT}/{i['mp3']}", f"{cn}/{i['name']}.mp3")
data = dict(cats=cats, items=items, allZip='zips/all-mp3.zip', allZipSize=os.path.getsize(f'{OUT}/zips/all-mp3.zip'))
json.dump(data, open(f'{OUT}/sounds.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(items), 'sounds,', len(cats), 'categories')
