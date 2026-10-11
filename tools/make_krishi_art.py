"""Regenerates the Krishi Paramarsha illustrations (SVG, 1200x630) and the PNG share-preview images.
Run from the project root:  python tools/make_krishi_art.py   (needs: pip install cairosvg)
To use real photos instead, just drop <slug>.jpg/.webp/.png into static/images/krishi/ -- they take priority."""
import math, random
W, H = 1200, 630

def head(sky, glow="#FFE9A8"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice"><defs>'
      f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sky[0]}"/><stop offset=".7" stop-color="{sky[1]}"/><stop offset="1" stop-color="{sky[2]}"/></linearGradient>'
      f'<radialGradient id="sun"><stop offset="0" stop-color="#FFF6D0"/><stop offset=".35" stop-color="#FFD76A"/><stop offset="1" stop-color="{glow}" stop-opacity="0"/></radialGradient>'
      '<linearGradient id="mist" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".55"/></linearGradient>'
      '<linearGradient id="vig" x1="0" y1="0" x2="0" y2="1"><stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#0b2414" stop-opacity=".38"/></linearGradient>'
      f'</defs><rect width="{W}" height="{H}" fill="url(#sky)"/><circle cx="930" cy="150" r="190" fill="url(#sun)"/>')

def sky_extras(r, birds=True):
    s = ""
    for x, y, w in [(140, 90, 150), (420, 150, 110), (700, 70, 130)]:
        s += f'<g fill="#fff" opacity=".7"><ellipse cx="{x}" cy="{y}" rx="{w}" ry="22"/><ellipse cx="{x+w*.4}" cy="{y-14}" rx="{w*.5}" ry="20"/></g>'
    if birds:
        for x, y in [(300, 120), (350, 95), (400, 130)]:
            s += f'<path d="M{x} {y} q10 -10 20 0 q10 -10 20 0" stroke="#33463a" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    return s

def far(r, base=330, c1="#9CCB9A", c2="#7DB67F", trees="#4F8F5A"):
    s = f'<path d="M0 {base-40} Q200 {base-110} 420 {base-50} T860 {base-70} T1200 {base-40} V{H} H0Z" fill="{c1}"/>'
    s += f'<path d="M0 {base} Q300 {base-60} 600 {base-10} T1200 {base-20} V{H} H0Z" fill="{c2}"/>'
    for i in range(46):
        x = r.randint(0, W); y = base - 8 + r.randint(-14, 6); rr = r.randint(14, 30)
        s += f'<circle cx="{x}" cy="{y}" r="{rr}" fill="{trees}" opacity=".55"/>'
    return s

def ground(top, c1, c2):
    return (f'<defs><linearGradient id="gr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
            f'<rect y="{top}" width="{W}" height="{H-top}" fill="url(#gr)"/>')

def finish(): return f'<rect width="{W}" height="{H}" fill="url(#vig)"/></svg>'

def paddy():
    r = random.Random(1); s = head(("#8FD0EA", "#CDEBF3", "#FBF1CF")) + sky_extras(r) + far(r, 300)
    s += ground(300, "#8CCB6B", "#3E8E3A")
    s += '<rect y="395" width="1200" height="235" fill="#79C3D6" opacity=".35"/><ellipse cx="930" cy="420" rx="110" ry="9" fill="#FFF3B8" opacity=".6"/>'
    for row in range(7):
        y = 360 + row * 42; sc = .55 + row * .17; n = 30 - row * 2
        for i in range(n):
            x = (i + .5) * (W / n) + r.randint(-8, 8)
            for k in range(5):
                a = -50 + k * 25; h = 70 * sc + r.randint(-8, 8)
                ex = x + math.sin(math.radians(a)) * h * .6; ey = y - math.cos(math.radians(a)) * h
                s += f'<path d="M{x:.0f} {y} Q{(x+ex)/2:.0f} {y-h*.7:.0f} {ex:.0f} {ey:.0f}" stroke="#3E8E3A" stroke-width="{2.4*sc:.1f}" fill="none" stroke-linecap="round"/>'
            if row >= 2:
                px = x + 10 * sc; py = y - 74 * sc
                s += f'<path d="M{x:.0f} {y} Q{x+4:.0f} {py+20:.0f} {px:.0f} {py:.0f} q{18*sc:.0f} {6*sc:.0f} {22*sc:.0f} {34*sc:.0f}" stroke="#D9A21F" stroke-width="{3*sc:.1f}" fill="none" stroke-linecap="round"/>'
                for g in range(6):
                    s += f'<ellipse cx="{px+g*3.4*sc+3:.0f}" cy="{py+g*5.5*sc:.0f}" rx="{2.2*sc:.1f}" ry="{4*sc:.1f}" fill="#F0C440"/>'
    return s + finish()

def potato():
    r = random.Random(2); s = head(("#9AD3EE", "#D8EEF4", "#FBF2D6")) + sky_extras(r) + far(r, 290, "#A8CF8E", "#86BA6F", "#5C9A55")
    s += ground(290, "#8A6038", "#4F321B")
    for i in range(9):
        y0 = 320 + i * 38; s += f'<path d="M-20 {y0+38} Q600 {y0-10-i*4} 1220 {y0+38}" stroke="#5E3F24" stroke-width="{16+i*5}" fill="none" opacity=".55"/><path d="M-20 {y0+30} Q600 {y0-18-i*4} 1220 {y0+30}" stroke="#A47A4D" stroke-width="3" fill="none" opacity=".35"/>'
    for row in range(5):
        y = 360 + row * 52; sc = .5 + row * .22; n = 14 - row
        for i in range(n):
            x = (i + .5) * (W / n) + r.randint(-10, 10)
            for k in range(7):
                a = r.randint(-70, 70); l = 34 * sc
                s += f'<ellipse cx="{x+math.sin(math.radians(a))*l:.0f}" cy="{y-18*sc-abs(math.cos(math.radians(a)))*l*.7:.0f}" rx="{15*sc:.0f}" ry="{9*sc:.0f}" transform="rotate({a} {x+math.sin(math.radians(a))*l:.0f} {y-18*sc-abs(math.cos(math.radians(a)))*l*.7:.0f})" fill="{r.choice(["#3E8E3A","#4FA044","#2F7D32"])}"/>'
            if r.random() < .5: s += f'<circle cx="{x+6:.0f}" cy="{y-48*sc:.0f}" r="{4*sc:.1f}" fill="#fff"/>'
    for (x, y, rx, ry, c) in [(260, 560, 62, 40, "#D2A15F"), (340, 585, 54, 34, "#C58F4B"), (190, 592, 50, 32, "#DDB26F"), (420, 560, 46, 30, "#D2A15F"), (300, 530, 46, 30, "#E0B676")]:
        s += f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{c}"/><ellipse cx="{x-rx*.3}" cy="{y-ry*.35}" rx="{rx*.35}" ry="{ry*.2}" fill="#fff" opacity=".28"/>'
        for d in range(3): s += f'<circle cx="{x+r.randint(-rx//2,rx//2)}" cy="{y+r.randint(-ry//3,ry//3)}" r="2.4" fill="#8A5E2C"/>'
    return s + finish()

def jute():
    r = random.Random(3); s = head(("#A5D7EA", "#DDEFD9", "#F4F2CE")) + sky_extras(r) + far(r, 300, "#9CC98A", "#78B365", "#4F8F4E")
    s += ground(300, "#6FB257", "#2F6F32")
    for layer in range(3):
        n = 30 + layer * 8; sc = .6 + layer * .3
        for i in range(n):
            x = r.randint(-10, W + 10); b = 470 + layer * 80; hgt = r.randint(260, 340) * sc
            tx = x + r.randint(-14, 14)
            s += f'<path d="M{x} {b} Q{x+4} {b-hgt/2:.0f} {tx} {b-hgt:.0f}" stroke="{["#7DB86A","#5FA14A","#4E8F3F"][layer]}" stroke-width="{4+layer*2}" fill="none" stroke-linecap="round"/>'
            for k in range(6):
                yy = b - hgt + 30 + k * hgt / 7; sd = 1 if k % 2 else -1
                s += f'<path d="M{x+(tx-x)*(1-(yy-(b-hgt))/hgt):.0f} {yy:.0f} q{sd*26*sc:.0f} {-10*sc:.0f} {sd*44*sc:.0f} {10*sc:.0f} q{-sd*22*sc:.0f} {-2*sc:.0f} {-sd*44*sc:.0f} {-10*sc:.0f}" fill="{["#5FAE57","#3E8E3A","#2F7D32"][layer]}" opacity=".95"/>'
    for i in range(16):
        x = 820 + i * 22; s += f'<path d="M{x} 360 Q{x+r.randint(-18,18)} 470 {x+r.randint(-10,10)} 600" stroke="{r.choice(["#E7C25A","#D6A93A","#F0D27A"])}" stroke-width="5" fill="none" stroke-linecap="round" opacity=".92"/>'
    s += '<rect x="800" y="352" width="400" height="12" rx="6" fill="#8B5E34"/>'
    return s + finish()

def mustard():
    r = random.Random(4); s = head(("#7FC4EA", "#C9E8F6", "#FFF6CF"), "#FFF0A8") + sky_extras(r) + far(r, 285, "#B8D07A", "#9CBE5A", "#5B8F3A")
    s += ground(285, "#F7CE2B", "#E3A800")
    for i in range(1700):
        t = r.random(); y = 295 + t ** 1.6 * 335; x = r.randint(0, W); rr = 1.2 + t * 6.5
        s += f'<circle cx="{x}" cy="{y:.0f}" r="{rr:.1f}" fill="{r.choice(["#FFE45C","#F9C70C","#FFD93B","#FFF08A","#F2B705"])}"/>'
    for i in range(46):
        x = r.randint(0, W); y = r.randint(500, 625); h = r.randint(70, 150)
        s += f'<path d="M{x} {y+60} Q{x+6} {y} {x+r.randint(-12,12)} {y-h+50}" stroke="#4F8F3A" stroke-width="4" fill="none"/>'
        for k in range(8):
            ax = x + r.randint(-24, 24); ay = y - h + 50 + r.randint(-18, 8)
            s += f'<circle cx="{ax}" cy="{ay}" r="{r.randint(7,10)}" fill="{r.choice(["#FFE45C","#FFD21F"])}"/><circle cx="{ax}" cy="{ay}" r="2.8" fill="#C27A00"/>'
    for bx, by in [(620, 470), (760, 420), (520, 540)]:
        s += f'<g transform="translate({bx} {by}) rotate(-12)"><ellipse cx="-6" cy="-10" rx="11" ry="6" fill="#fff" opacity=".7"/><ellipse cx="8" cy="-12" rx="11" ry="6" fill="#fff" opacity=".7"/><ellipse rx="13" ry="8" fill="#F2B705"/><rect x="-5" y="-8" width="4" height="16" fill="#3a2a05"/><rect x="3" y="-7" width="4" height="14" fill="#3a2a05"/></g>'
    return s + finish()

def brinjal():
    r = random.Random(5); s = head(("#A6D8EE", "#DDEEE2", "#F7F1D4")) + sky_extras(r) + far(r, 300, "#A9D28F", "#86BB70", "#5C9A56")
    s += ground(300, "#7A5636", "#432B17")
    for i in range(8):
        y0 = 340 + i * 40; s += f'<path d="M-20 {y0+34} Q600 {y0-10} 1220 {y0+34}" stroke="#573A21" stroke-width="{18+i*5}" fill="none" opacity=".5"/>'
    for (x, sc) in [(150, .9), (420, 1.1), (700, .95), (980, 1.15), (1150, .8)]:
        y = 560 if sc > 1 else 540
        s += f'<g transform="translate({x} {y}) scale({sc})"><path d="M0 40 V-150" stroke="#4A8A3A" stroke-width="12" stroke-linecap="round"/>'
        for (lx, ly, a) in [(-80, -120, -20), (70, -130, 15), (-60, -60, -10), (80, -55, 10), (0, -180, 0), (-30, -20, 0)]:
            s += f'<ellipse cx="{lx}" cy="{ly}" rx="58" ry="28" transform="rotate({a} {lx} {ly})" fill="{r.choice(["#3E8E3A","#4FA044","#3A8238"])}"/><path d="M{lx-40} {ly} H{lx+40}" stroke="#2F6F32" stroke-width="2" transform="rotate({a} {lx} {ly})"/>'
        for (fx, fy, a) in [(-34, -30, 10), (34, -22, -12), (-4, -78, 4)]:
            s += f'<g transform="translate({fx} {fy}) rotate({a})"><path d="M-14 0 C-24 40 -16 78 0 84 C16 78 24 40 14 0Z" fill="#5A2A86"/><path d="M-9 8 C-14 38 -10 62 -4 74" stroke="#fff" stroke-width="5" opacity=".28" fill="none" stroke-linecap="round"/><path d="M-17 -2 q17 -12 34 0 l-4 10 q-13 6 -26 0Z" fill="#3E8E3A"/></g>'
        s += '</g>'
    return s + finish()

if __name__ == "__main__":
    import cairosvg
    for n, f in dict(paddy=paddy, potato=potato, jute=jute, mustard=mustard, brinjal=brinjal).items():
        svg = f(); open(f"static/images/krishi/{n}.svg", "w", encoding="utf-8").write(svg)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=f"static/images/krishi/og/{n}.png", output_width=1200, output_height=630)
        print(n, len(svg) // 1024, "KB")
