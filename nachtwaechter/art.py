# -*- coding: utf-8 -*-
"""SVG-Zeichnungen der Figuren und neuer Hintergründe.

Jede Funktion liefert einen SVG-String. build() rendert alle Varianten per
Chromium (svg2png.js) nach build/art/*.png.
"""
import os, json, subprocess, itertools

ROOT = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(ROOT, "build", "art")
os.makedirs(ART, exist_ok=True)


def svg(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs>{defs}'
            '<filter id="b2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2"/></filter>'
            '<filter id="b6" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>'
            '<filter id="b14" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>'
            '<filter id="b30" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="30"/></filter>'
            f'</defs>{body}</svg>')


def mirror(path_d, cx=450):
    """Spiegelt Pfade aus absoluten Koordinatenpaaren (M/L/C/Q/Z) an x=cx."""
    import re
    toks = re.findall(r"[A-Za-z]|-?\d+\.?\d*", path_d)
    out, nums = [], []
    for t in toks:
        if t.isalpha():
            out.append(t)
        else:
            nums.append(float(t))
            if len(nums) == 2:
                out.append(f"{2 * cx - nums[0]:.1f},{nums[1]:.1f}")
                nums = []
    return " ".join(out)


# =====================================================================
#  WALTER
# =====================================================================
def walter(eyes="open", mouth="0", brows="normal", wet=False, light="warm"):
    defs = """
    <radialGradient id="wskin" cx="0.42" cy="0.42" r="0.7">
      <stop offset="0" stop-color="#e4bba2"/><stop offset="0.55" stop-color="#b9876f"/><stop offset="1" stop-color="#6b4536"/></radialGradient>
    <linearGradient id="wneck" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6e4a3c"/><stop offset="1" stop-color="#9c705c"/></linearGradient>
    <linearGradient id="wjacket" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#34405a"/><stop offset="1" stop-color="#0f131c"/></linearGradient>
    <linearGradient id="wcap" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a3349"/><stop offset="1" stop-color="#0c0f17"/></linearGradient>
    <linearGradient id="wlight" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff2e0" stop-opacity="0"/><stop offset="0.55" stop-color="#000" stop-opacity="0.05"/><stop offset="1" stop-color="#000" stop-opacity="0.6"/></linearGradient>
    <clipPath id="wclip"><path d="M332,365 C310,425 306,505 326,572 C346,640 400,690 450,693 C500,690 554,640 574,572 C594,505 590,425 568,365 Z"/>
      <rect x="390" y="590" width="122" height="170"/><ellipse cx="312" cy="485" rx="28" ry="52"/><ellipse cx="588" cy="485" rx="28" ry="52"/></clipPath>
    """
    b = []
    # Körper / Jacke
    b.append('<path d="M20,1100 C40,930 120,830 290,792 C345,778 382,760 395,722 L505,722 C518,760 555,778 610,792 C780,830 860,930 880,1100 Z" fill="url(#wjacket)"/>')
    b.append('<path d="M395,722 L450,862 L505,722 Z" fill="#8ea2b6"/>')
    b.append('<path d="M438,770 L462,770 L472,905 L450,935 L428,905 Z" fill="#141720"/>')
    b.append('<path d="M395,722 L450,862 L372,1010 L292,800 C345,785 382,762 395,722 Z" fill="#202a3d" stroke="#0a0d14" stroke-width="4"/>')
    b.append('<path d="M505,722 L450,862 L528,1010 L608,800 C555,785 518,762 505,722 Z" fill="#1b2335" stroke="#0a0d14" stroke-width="4"/>')
    b.append('<rect x="600" y="880" width="160" height="48" rx="6" fill="#b8951f" opacity="0.85"/>'
             '<text x="680" y="913" font-family="DejaVu Sans, Arial" font-weight="bold" font-size="21" text-anchor="middle" fill="#14110a">SICHERHEIT</text>')
    b.append('<path d="M150,840 L290,795 L300,822 L165,868 Z" fill="#0b0e15"/><path d="M750,840 L610,795 L600,822 L735,868 Z" fill="#0b0e15"/>')
    # Hals
    b.append('<path d="M392,595 L508,595 L512,738 Q450,775 388,738 Z" fill="url(#wneck)"/>')
    b.append('<path d="M410,690 Q450,705 490,690" stroke="#5a3a2e" stroke-width="3" fill="none" opacity="0.6"/>')
    # Ohren
    for cx in (312, 588):
        b.append(f'<ellipse cx="{cx}" cy="485" rx="27" ry="52" fill="#a8775f"/><ellipse cx="{cx}" cy="487" rx="13" ry="30" fill="#7a4f3f"/>')
    # Kopf
    b.append('<path d="M332,365 C310,425 306,505 326,572 C346,640 400,690 450,693 C500,690 554,640 574,572 C594,505 590,425 568,365 Z" fill="url(#wskin)"/>')
    # graue Haare an den Schläfen
    b.append('<path d="M300,372 C290,420 296,470 310,455 C316,420 326,395 340,372 Z" fill="#a3a3a3"/>')
    b.append('<path d="M600,372 C610,420 604,470 590,455 C584,420 574,395 560,372 Z" fill="#9a9a9a"/>')
    # Stirnfalten
    for y in (388, 400):
        b.append(f'<path d="M385,{y} Q450,{y - 6} 515,{y}" stroke="#7d5444" stroke-width="2.5" fill="none" opacity="0.55"/>')
    # Augenhöhlen
    for cx in (393, 507):
        b.append(f'<ellipse cx="{cx}" cy="460" rx="44" ry="26" fill="#3a2016" opacity="0.28" filter="url(#b6)"/>')
        b.append(f'<path d="M{cx - 26},482 Q{cx},494 {cx + 26},482" stroke="#6a4232" stroke-width="3" fill="none" opacity="0.55"/>')
    # Augen
    for cx in (393, 507):
        if eyes in ("open", "serious"):
            b.append(f'<ellipse cx="{cx}" cy="459" rx="21" ry="11" fill="#e6dccf"/>'
                     f'<circle cx="{cx + 2}" cy="460" r="9" fill="#3e5163"/><circle cx="{cx + 2}" cy="460" r="4.5" fill="#050505"/>'
                     f'<circle cx="{cx + 5}" cy="456" r="2.2" fill="#fff"/>'
                     f'<path d="M{cx - 23},458 Q{cx},440 {cx + 23},458" stroke="#3a2219" stroke-width="5" fill="none"/>')
        elif eyes == "closed":
            b.append(f'<path d="M{cx - 22},461 Q{cx},471 {cx + 22},461" stroke="#3a2219" stroke-width="5" fill="none"/>')
        elif eyes == "black":
            b.append(f'<ellipse cx="{cx}" cy="458" rx="26" ry="16" fill="#020202"/><circle cx="{cx + 6}" cy="453" r="2" fill="#ffdddd"/>')
            b.append(f'<path d="M{cx - 28},470 Q{cx - 30},500 {cx - 18},530" stroke="#1a0a08" stroke-width="2" fill="none" opacity="0.6"/>')
    # Brauen
    if brows == "serious" or eyes == "serious":
        lb = "M350,428 C372,414 410,418 436,432 C410,428 376,428 353,440 Z"
    elif eyes == "black":
        lb = "M350,418 C372,398 410,400 436,416 C410,412 376,414 353,430 Z"
    else:
        lb = "M350,424 C372,404 410,402 434,418 C410,414 376,418 353,434 Z"
    b.append(f'<path d="{lb}" fill="#c4c4c4" stroke="#8d8d8d" stroke-width="2"/>')
    b.append(f'<path d="{mirror(lb)}" fill="#bdbdbd" stroke="#8d8d8d" stroke-width="2"/>')
    # Nase
    b.append('<path d="M438,452 C436,490 424,515 418,532 C426,550 444,553 450,550 C456,553 474,550 482,532 C476,515 464,490 462,452 Z" fill="#b07c64"/>')
    b.append('<path d="M438,452 C436,490 424,515 418,532 C426,550 440,552 446,549 C440,520 444,480 448,452 Z" fill="#8c5d49" opacity="0.6"/>')
    b.append('<ellipse cx="436" cy="541" rx="8" ry="4" fill="#3a1e16"/><ellipse cx="464" cy="541" rx="8" ry="4" fill="#3a1e16"/>')
    b.append('<ellipse cx="456" cy="505" rx="6" ry="16" fill="#f0cdb8" opacity="0.35" filter="url(#b2)"/>')
    # Nasolabialfalten / Hängebacken
    b.append('<path d="M416,536 C398,560 392,592 398,622" stroke="#6a4436" stroke-width="4" fill="none" opacity="0.6"/>')
    b.append('<path d="M484,536 C502,560 508,592 502,622" stroke="#6a4436" stroke-width="4" fill="none" opacity="0.6"/>')
    b.append('<path d="M350,600 C356,640 380,668 408,680" stroke="#6a4436" stroke-width="3" fill="none" opacity="0.4"/>')
    b.append('<path d="M550,600 C544,640 520,668 492,680" stroke="#6a4436" stroke-width="3" fill="none" opacity="0.4"/>')
    # Mund
    if mouth == "0":
        b.append('<path d="M418,606 Q450,612 482,606" stroke="#3a1c18" stroke-width="5" fill="none"/>')
    elif mouth == "1":
        b.append('<ellipse cx="450" cy="608" rx="25" ry="9" fill="#2a0c0c"/><path d="M428,603 L472,603" stroke="#cfc4b0" stroke-width="3"/>')
    elif mouth == "2":
        b.append('<ellipse cx="450" cy="612" rx="29" ry="19" fill="#240909"/><path d="M426,600 Q450,596 474,600 L472,606 Q450,602 428,606 Z" fill="#d8ccb6"/>')
    elif mouth == "grin":
        b.append('<path d="M345,585 Q450,700 555,585 Q450,640 345,585 Z" fill="#120303" stroke="#2a0a08" stroke-width="3"/>')
        for i in range(13):
            x = 368 + i * 13.5
            yt = 596 + 0.0026 * (x - 450) ** 2 * 1.0
            b.append(f'<path d="M{x},{yt + 2} L{x + 6},{yt + 18} L{x + 12},{yt + 2} Z" fill="#d9d2bf"/>')
        for i in range(11):
            x = 382 + i * 13.5
            yb = 655 - 0.006 * (x - 450) ** 2
            b.append(f'<path d="M{x},{yb} L{x + 6},{yb - 15} L{x + 12},{yb} Z" fill="#c9c0aa"/>')
    b.append('<path d="M425,628 Q450,636 475,628" stroke="#6a4436" stroke-width="3" fill="none" opacity="0.5"/>')
    # Schnurrbart
    b.append('<path d="M383,588 C392,560 430,553 450,566 C470,553 508,560 517,588 C522,603 500,600 485,594 C470,589 460,585 450,587 C440,585 430,589 415,594 C400,600 378,603 383,588 Z" fill="#cfcfcf" stroke="#8a8a8a" stroke-width="2"/>')
    for i in range(9):
        x = 395 + i * 14
        b.append(f'<path d="M{x},{570 + abs(450 - x) * 0.12} l{(-4 if x < 450 else 4)},{18}" stroke="#9c9c9c" stroke-width="2"/>')
    # Brille
    b.append('<g fill="none" stroke="#262626" stroke-width="5">'
             '<rect x="345" y="430" width="98" height="60" rx="22"/><rect x="457" y="430" width="98" height="60" rx="22"/>'
             '<path d="M443,452 Q450,444 457,452"/><path d="M345,452 L312,460"/><path d="M555,452 L588,460"/></g>')
    b.append('<path d="M360,440 L380,440 L355,478 Z" fill="#fff" opacity="0.08"/><path d="M472,440 L492,440 L467,478 Z" fill="#fff" opacity="0.08"/>')
    # Licht / Schatten (Hautbereich)
    b.append('<g clip-path="url(#wclip)"><rect x="250" y="300" width="400" height="500" fill="url(#wlight)"/></g>')
    b.append('<path d="M574,420 C592,505 580,600 520,672" stroke="#9fd2ff" stroke-width="7" fill="none" opacity="0.35" filter="url(#b2)"/>')
    # Schatten des Mützenschirms
    b.append('<ellipse cx="450" cy="405" rx="175" ry="34" fill="#000" opacity="0.4" filter="url(#b6)"/>')
    # Mütze
    b.append('<path d="M298,374 C292,272 360,230 450,228 C540,230 608,272 602,374 Z" fill="url(#wcap)"/>')
    b.append('<rect x="298" y="338" width="304" height="38" fill="#0b0e15"/>')
    b.append('<path d="M450,276 L476,288 L472,318 L450,332 L428,318 L424,288 Z" fill="#b7952c" stroke="#5a4510" stroke-width="2"/>')
    b.append('<path d="M283,374 C350,354 550,354 617,374 C603,410 522,426 450,427 C378,426 297,410 283,374 Z" fill="#06070b"/>')
    b.append('<path d="M290,374 C350,358 550,358 610,374" stroke="#4a5470" stroke-width="3" fill="none" opacity="0.7"/>')
    if wet:
        for (x, y, l) in ((370, 520, 30), (530, 470, 40), (420, 640, 26), (560, 600, 34), (330, 560, 22), (480, 400, 18)):
            b.append(f'<path d="M{x},{y} q3,{l / 2} 0,{l}" stroke="#d6ecff" stroke-width="4" opacity="0.55" fill="none"/>')
            b.append(f'<circle cx="{x}" cy="{y + l}" r="4" fill="#e6f4ff" opacity="0.6"/>')
    return svg(900, 1100, "".join(b), defs)


def walter_back():
    """Walter von hinten, ganze Figur (geht in den Regen / steht im Gang)."""
    b = ['<ellipse cx="200" cy="885" rx="120" ry="14" fill="#000" opacity="0.5" filter="url(#b6)"/>',
         # Beine
         '<path d="M150,600 L140,870 L185,870 L198,610 Z" fill="#14161c"/><path d="M250,600 L262,870 L218,870 L205,610 Z" fill="#111318"/>',
         '<path d="M128,860 L190,860 L192,885 L122,885 Z" fill="#050506"/><path d="M212,860 L275,860 L280,885 L210,885 Z" fill="#050506"/>',
         # Mantel
         '<path d="M110,250 C130,200 270,200 290,250 L320,640 C260,660 140,660 80,640 Z" fill="#1d2230"/>',
         '<path d="M200,230 L200,650" stroke="#10131b" stroke-width="5"/>',
         '<path d="M110,250 C95,350 92,470 100,560" stroke="#0e1018" stroke-width="40" stroke-linecap="round" fill="none"/>',
         '<path d="M290,250 C305,350 308,470 300,560" stroke="#0e1018" stroke-width="40" stroke-linecap="round" fill="none"/>',
         '<ellipse cx="100" cy="580" rx="20" ry="26" fill="#8c6150"/><ellipse cx="300" cy="580" rx="20" ry="26" fill="#8c6150"/>',
         '<rect x="128" y="300" width="144" height="34" fill="#b8951f" opacity="0.75"/>',
         '<text x="200" y="324" font-family="DejaVu Sans, Arial" font-weight="bold" font-size="20" text-anchor="middle" fill="#14110a">SICHERHEIT</text>',
         # Kragen / Kopf
         '<path d="M140,215 C160,190 240,190 260,215 L250,250 L150,250 Z" fill="#232838"/>',
         '<rect x="172" y="190" width="56" height="40" fill="#8a5f4e"/>',
         '<ellipse cx="200" cy="150" rx="62" ry="72" fill="#9c9c9c"/>',
         '<path d="M150,120 C160,170 175,200 200,210 M250,120 C240,170 225,200 200,210 M200,120 L200,205 M175,125 C178,170 188,195 196,206 M225,125 C222,170 212,195 204,206" stroke="#7a7a7a" stroke-width="3" fill="none"/>',
         '<path d="M150,190 C170,215 230,215 250,190 L248,205 C230,225 170,225 152,205 Z" fill="#8a5f4e"/>',
         '<ellipse cx="138" cy="150" rx="12" ry="22" fill="#7a4f3f"/><ellipse cx="262" cy="150" rx="12" ry="22" fill="#7a4f3f"/>',
         '<path d="M134,128 C130,70 170,48 200,48 C230,48 270,70 266,128 Z" fill="#141a28"/>',
         '<rect x="134" y="112" width="132" height="20" fill="#0a0d14"/>']
    return svg(400, 900, "".join(b))


# =====================================================================
#  JONAS
# =====================================================================
def jonas(eyes="open", mouth="0", light="cold"):
    defs = """
    <radialGradient id="jskin" cx="0.45" cy="0.42" r="0.7">
      <stop offset="0" stop-color="#ecc6ad"/><stop offset="0.6" stop-color="#c49274"/><stop offset="1" stop-color="#7a5040"/></radialGradient>
    <linearGradient id="jjacket" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#262b36"/><stop offset="1" stop-color="#0a0c10"/></linearGradient>
    <linearGradient id="jhair" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b2a20"/><stop offset="1" stop-color="#1a120d"/></linearGradient>
    <linearGradient id="jlight" x1="0" y1="0" x2="1" y2="0.3">
      <stop offset="0" stop-color="#000" stop-opacity="0.0"/><stop offset="0.5" stop-color="#000" stop-opacity="0.08"/><stop offset="1" stop-color="#000" stop-opacity="0.62"/></linearGradient>
    <clipPath id="jclip"><path d="M336,380 C320,450 322,522 340,586 C360,646 410,690 450,693 C490,690 540,646 560,586 C578,522 580,450 564,380 Z"/>
      <rect x="400" y="600" width="100" height="160"/></clipPath>
    """
    b = []
    b.append('<path d="M40,1100 C60,940 140,845 300,808 C350,796 388,780 402,742 L498,742 C512,780 550,796 600,808 C760,845 840,940 860,1100 Z" fill="url(#jjacket)"/>')
    b.append('<path d="M318,790 C330,730 570,730 582,790 C560,830 340,830 318,790 Z" fill="#4c525d"/>')  # Kapuze
    b.append('<path d="M402,742 L450,880 L498,742 Z" fill="#5a606b"/>')  # Hoodie
    b.append('<path d="M436,800 L432,900 M464,800 L468,900" stroke="#c9ccd2" stroke-width="5"/>')  # Kordeln
    b.append('<path d="M450,880 L450,1100" stroke="#050608" stroke-width="6"/>')  # Reißverschluss
    b.append('<rect x="560" y="900" width="150" height="44" rx="6" fill="#b8951f" opacity="0.85"/>'
             '<text x="635" y="930" font-family="DejaVu Sans, Arial" font-weight="bold" font-size="20" text-anchor="middle" fill="#14110a">SICHERHEIT</text>')
    b.append('<path d="M405,600 L495,600 L500,750 Q450,780 400,750 Z" fill="#a8775f"/>')
    for cx in (318, 582):
        b.append(f'<ellipse cx="{cx}" cy="492" rx="24" ry="46" fill="#c08a70"/><ellipse cx="{cx}" cy="494" rx="11" ry="26" fill="#8e5c48"/>')
    b.append('<path d="M336,380 C320,450 322,522 340,586 C360,646 410,690 450,693 C490,690 540,646 560,586 C578,522 580,450 564,380 Z" fill="url(#jskin)"/>')
    b.append('<path d="M350,590 C370,650 420,688 450,690 C480,688 530,650 550,590 C520,640 480,660 450,660 C420,660 380,640 350,590 Z" fill="#3a2a22" opacity="0.18"/>')  # Bartschatten
    # Brauen
    if eyes == "wide":
        lb = "M356,420 C376,404 410,402 432,410 C410,412 380,416 360,430 Z"
    else:
        lb = "M354,432 C376,418 410,416 434,424 C410,424 380,428 358,440 Z"
    b.append(f'<path d="{lb}" fill="#2a1c14"/><path d="{mirror(lb)}" fill="#2a1c14"/>')
    for cx in (395, 505):
        b.append(f'<ellipse cx="{cx}" cy="468" rx="40" ry="24" fill="#4a2a1e" opacity="0.2" filter="url(#b6)"/>')
        if eyes in ("open", "wide"):
            ry = 15 if eyes == "wide" else 11
            pr = 7 if eyes == "wide" else 9
            b.append(f'<ellipse cx="{cx}" cy="466" rx="23" ry="{ry}" fill="#efe8e0"/>'
                     f'<circle cx="{cx + 1}" cy="466" r="{pr + 3}" fill="#5c3b25"/><circle cx="{cx + 1}" cy="466" r="{pr - 3}" fill="#050505"/>'
                     f'<circle cx="{cx + 4}" cy="462" r="2.4" fill="#fff"/>'
                     f'<path d="M{cx - 25},{466 - ry + 6} Q{cx},{466 - ry - 12} {cx + 25},{466 - ry + 6}" stroke="#20140e" stroke-width="5" fill="none"/>')
        else:
            b.append(f'<path d="M{cx - 23},468 Q{cx},478 {cx + 23},468" stroke="#20140e" stroke-width="5" fill="none"/>')
    b.append('<path d="M442,462 C440,500 430,525 428,540 C436,552 448,554 452,552 C456,554 466,552 472,540 C468,525 460,500 458,462 Z" fill="#c08b70"/>')
    b.append('<path d="M442,462 C440,500 430,525 428,540 C436,552 444,553 448,551 C444,520 446,490 449,462 Z" fill="#9a6a54" opacity="0.6"/>')
    b.append('<ellipse cx="441" cy="546" rx="6" ry="3" fill="#4a2a1e"/><ellipse cx="459" cy="546" rx="6" ry="3" fill="#4a2a1e"/>')
    if mouth == "0":
        b.append('<path d="M420,606 Q450,612 480,606" stroke="#7a3e3a" stroke-width="5" fill="none"/>')
    elif mouth == "1":
        b.append('<ellipse cx="450" cy="608" rx="20" ry="8" fill="#2a0c0c"/><path d="M432,606 Q450,598 468,606" stroke="#9a5650" stroke-width="3" fill="none"/>')
    else:
        b.append('<ellipse cx="450" cy="612" rx="23" ry="16" fill="#260a0a"/><path d="M432,601 L468,601" stroke="#e0d8c8" stroke-width="4"/>')
    b.append('<path d="M432,628 Q450,634 468,628" stroke="#9a6a54" stroke-width="3" fill="none" opacity="0.5"/>')
    b.append('<g clip-path="url(#jclip)"><rect x="300" y="350" width="300" height="420" fill="url(#jlight)"/></g>')
    b.append('<path d="M562,430 C578,505 570,590 520,665" stroke="#9fd2ff" stroke-width="6" fill="none" opacity="0.35" filter="url(#b2)"/>')
    # Haare
    b.append('<path d="M300,430 C285,300 345,212 452,208 C560,210 622,292 604,432 C596,395 582,365 566,356 C548,380 508,372 478,360 C440,385 390,372 356,360 C338,380 318,400 300,430 Z" fill="url(#jhair)"/>')
    for d in ("M360,250 Q338,214 395,232", "M430,215 Q428,182 470,210", "M510,228 Q545,200 552,250",
              "M560,280 Q600,272 585,320", "M318,330 Q290,312 330,290", "M470,360 Q462,398 440,365",
              "M400,365 Q384,400 372,368"):
        b.append(f'<path d="{d} Z" fill="#24180f"/>')
    b.append('<path d="M370,260 C410,236 470,232 520,250" stroke="#5a4232" stroke-width="6" fill="none" opacity="0.5"/>')
    return svg(900, 1100, "".join(b), defs)


def jonas_back():
    """Über-die-Schulter: Jonas von hinten mit Taschenlampe (1000x900)."""
    b = ['<path d="M-40,900 C-20,720 60,640 200,610 L420,600 C560,612 660,650 720,700 L760,900 Z" fill="#101319"/>',
         '<path d="M150,700 L620,690" stroke="#9aa2ad" stroke-width="22" opacity="0.35"/>',
         '<text x="380" y="770" font-family="DejaVu Sans, Arial" font-weight="bold" font-size="54" text-anchor="middle" fill="#c8ccd2" opacity="0.55">SICHERHEIT</text>',
         # Arm nach vorne
         '<path d="M520,630 C620,590 690,510 745,425 L835,480 C780,570 710,650 650,720 Z" fill="#141820"/>',
         '<path d="M745,425 L835,480" stroke="#2a303c" stroke-width="10"/>',
         '<ellipse cx="790" cy="452" rx="34" ry="28" fill="#a8775f"/>',
         '<path d="M770,420 L880,330 L905,358 L795,450 Z" fill="#2c2f36"/>',
         '<path d="M872,318 L915,352 L925,330 L888,300 Z" fill="#d8d8d0"/>',
         # Kopf von hinten
         '<path d="M300,610 C300,560 420,560 420,610 Z" fill="#8e604c"/>',
         '<ellipse cx="360" cy="440" rx="120" ry="140" fill="#1e150f"/>',
         '<ellipse cx="240" cy="470" rx="18" ry="34" fill="#9a6a54"/><ellipse cx="480" cy="470" rx="18" ry="34" fill="#8a5c48"/>',
         '<path d="M250,400 L230,350 L285,380 M330,310 L320,270 L360,305 M420,320 L455,280 L450,340 M460,400 L500,385 L475,430" fill="#2a1d14"/>',
         '<path d="M290,360 C330,330 400,330 440,360" stroke="#4a3426" stroke-width="8" fill="none" opacity="0.6"/>',
         '<path d="M478,330 C500,400 500,470 480,540" stroke="#9fd2ff" stroke-width="6" fill="none" opacity="0.3" filter="url(#b2)"/>']
    return svg(1000, 900, "".join(b))


# =====================================================================
#  MIA
# =====================================================================
def mia(eyes="open", mouth="0"):
    defs = """
    <radialGradient id="mskin" cx="0.48" cy="0.45" r="0.65">
      <stop offset="0" stop-color="#f3ddd0"/><stop offset="0.6" stop-color="#d9b9a8"/><stop offset="1" stop-color="#93736a"/></radialGradient>
    <linearGradient id="mcoat" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f2cf2a"/><stop offset="0.6" stop-color="#c79f12"/><stop offset="1" stop-color="#6e5506"/></linearGradient>
    <radialGradient id="mvig" cx="0.5" cy="0.5" r="0.55"><stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.55"/></radialGradient>
    <clipPath id="mclip"><path d="M335,520 C335,430 385,385 450,385 C515,385 565,430 565,520 C565,612 515,672 450,674 C385,672 335,612 335,520 Z"/></clipPath>
    """
    b = []
    b.append('<path d="M110,1100 C140,925 250,842 340,818 L560,818 C650,842 760,925 790,1100 Z" fill="url(#mcoat)"/>')
    b.append('<path d="M450,830 L450,1100" stroke="#7a5d08" stroke-width="5"/>')
    for y in (890, 970, 1050):
        b.append(f'<circle cx="485" cy="{y}" r="13" fill="#3a2c06"/><circle cx="481" cy="{y - 4}" r="4" fill="#8a7020"/>')
    # Kapuze außen
    b.append('<path d="M245,640 C210,390 318,215 450,212 C582,215 690,390 655,640 C640,712 600,778 560,822 L340,822 C300,778 260,712 245,640 Z" fill="url(#mcoat)"/>')
    b.append('<path d="M300,250 C340,230 380,222 420,220" stroke="#fff3a8" stroke-width="10" fill="none" opacity="0.4" filter="url(#b2)"/>')
    # Kapuze innen
    b.append('<path d="M298,566 C288,404 360,300 450,298 C540,300 612,404 602,566 C592,656 540,728 450,732 C360,728 308,656 298,566 Z" fill="#2c2104"/>')
    # Hals / Gesicht
    b.append('<path d="M410,650 L490,650 L496,740 L404,740 Z" fill="#b39486"/>')
    b.append('<path d="M335,520 C335,430 385,385 450,385 C515,385 565,430 565,520 C565,612 515,672 450,674 C385,672 335,612 335,520 Z" fill="url(#mskin)"/>')
    # Wangen + Sommersprossen
    b.append('<ellipse cx="385" cy="585" rx="30" ry="18" fill="#e08a8a" opacity="0.25" filter="url(#b6)"/>')
    b.append('<ellipse cx="515" cy="585" rx="30" ry="18" fill="#e08a8a" opacity="0.25" filter="url(#b6)"/>')
    for (x, y) in ((395, 565), (405, 575), (385, 578), (505, 565), (515, 575), (495, 578)):
        b.append(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#a0685a" opacity="0.6"/>')
    # Augen
    for cx in (405, 495):
        b.append(f'<ellipse cx="{cx}" cy="530" rx="36" ry="28" fill="#5a3a3a" opacity="0.22" filter="url(#b6)"/>')
        if eyes == "open":
            b.append(f'<ellipse cx="{cx}" cy="528" rx="25" ry="21" fill="#f4f0ec"/>'
                     f'<circle cx="{cx + 1}" cy="530" r="16" fill="#4a3020"/><circle cx="{cx + 1}" cy="530" r="8" fill="#050505"/>'
                     f'<circle cx="{cx + 7}" cy="523" r="4.5" fill="#fff"/><circle cx="{cx - 5}" cy="537" r="2" fill="#fff"/>'
                     f'<path d="M{cx - 27},526 Q{cx},500 {cx + 27},526" stroke="#1a100c" stroke-width="4" fill="none"/>')
            for k in (-1, 0, 1):
                b.append(f'<path d="M{cx + k * 12},{506 + abs(k) * 3} l{k * 4},-9" stroke="#1a100c" stroke-width="2.5"/>')
        elif eyes == "closed":
            b.append(f'<path d="M{cx - 24},530 Q{cx},542 {cx + 24},530" stroke="#1a100c" stroke-width="4" fill="none"/>')
        else:  # black
            b.append(f'<ellipse cx="{cx}" cy="528" rx="28" ry="24" fill="#010101"/><circle cx="{cx + 7}" cy="521" r="2.2" fill="#fff"/>')
            b.append(f'<path d="M{cx - 20},552 Q{cx - 24},590 {cx - 14},620" stroke="#1a0a0a" stroke-width="3" fill="none" opacity="0.7"/>')
    # Brauen
    lb = "M378,488 Q400,476 424,484" if eyes != "black" else "M378,494 Q402,500 426,480"
    b.append(f'<path d="{lb}" stroke="#5a3a2a" stroke-width="5" fill="none" stroke-linecap="round"/>')
    b.append(f'<path d="{mirror(lb)}" stroke="#5a3a2a" stroke-width="5" fill="none" stroke-linecap="round"/>')
    # Nase
    b.append('<path d="M444,572 Q450,582 456,572" stroke="#a07868" stroke-width="3" fill="none"/>')
    # Mund
    if mouth == "0":
        b.append('<path d="M430,612 Q450,624 470,612" stroke="#8a4448" stroke-width="4" fill="none" stroke-linecap="round"/>')
    elif mouth == "1":
        b.append('<ellipse cx="450" cy="616" rx="12" ry="7" fill="#3a0e12"/>')
    elif mouth == "2":
        b.append('<ellipse cx="450" cy="618" rx="15" ry="12" fill="#3a0e12"/>')
    elif mouth == "grin":
        b.append('<path d="M352,592 Q450,700 548,592 Q450,640 352,592 Z" fill="#100204" stroke="#3a0a0e" stroke-width="3"/>')
        for i in range(12):
            x = 368 + i * 14
            yt = 600 + 0.0022 * (x - 450) ** 2 * 0.0 + (0.0 if True else 0)
            yt = 597 + 0.004 * abs(x - 450) * 3
            b.append(f'<path d="M{x},{yt} L{x + 7},{yt + 16} L{x + 14},{yt} Z" fill="#e6e0d0"/>')
        for i in range(10):
            x = 384 + i * 14
            yb = 660 - 0.0055 * (x - 450) ** 2
            b.append(f'<path d="M{x},{yb} L{x + 7},{yb - 14} L{x + 14},{yb} Z" fill="#d8d0bc"/>')
    # nasse Haarsträhnen
    b.append('<path d="M335,500 C340,410 400,372 470,384 C430,392 400,420 385,470 C375,440 360,460 350,500 Z" fill="#1c1410"/>')
    b.append('<path d="M565,500 C560,410 500,372 430,384 C470,392 500,420 515,470 C525,440 540,460 550,500 Z" fill="#1c1410"/>')
    for d in ("M338,470 C330,540 336,600 352,650", "M352,470 C346,530 350,580 362,620",
              "M562,470 C570,540 564,600 548,650", "M548,470 C554,530 550,580 538,620"):
        b.append(f'<path d="{d}" stroke="#1c1410" stroke-width="12" fill="none" stroke-linecap="round"/>')
    b.append('<path d="M400,400 C420,392 440,390 460,392" stroke="#6a5a50" stroke-width="4" fill="none" opacity="0.6"/>')
    # Tropfen
    for (x, y) in ((360, 700), (540, 690), (470, 690)):
        b.append(f'<path d="M{x},{y} q-6,12 0,18 q6,-6 0,-18 Z" fill="#cfe6ff" opacity="0.6"/>')
    return svg(900, 1100, "".join(b), defs)


def mia_sitting():
    defs = """<linearGradient id="mc2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f2cf2a"/><stop offset="1" stop-color="#8a6a08"/></linearGradient>"""
    b = ['<ellipse cx="250" cy="650" rx="170" ry="18" fill="#000" opacity="0.55" filter="url(#b6)"/>',
         # Stiefel
         '<path d="M170,520 L235,520 L240,640 L150,640 Q140,610 172,600 Z" fill="#b01c1c"/>',
         '<path d="M265,520 L330,520 L345,640 L255,640 Q248,605 268,600 Z" fill="#a01818"/>',
         '<path d="M150,632 L240,632 L240,645 L148,645 Z" fill="#3a0606"/><path d="M255,632 L345,632 L347,645 L255,645 Z" fill="#3a0606"/>',
         # Mantel / Knie
         '<path d="M150,260 C170,215 330,215 350,260 L380,500 C330,540 170,540 120,500 Z" fill="url(#mc2)"/>',
         '<ellipse cx="200" cy="470" rx="62" ry="58" fill="#d8b220"/><ellipse cx="300" cy="470" rx="62" ry="58" fill="#c9a41a"/>',
         # Hase
         '<ellipse cx="250" cy="420" rx="58" ry="52" fill="#8e8e94"/><ellipse cx="250" cy="355" rx="44" ry="40" fill="#9a9aa0"/>',
         '<path d="M225,330 C200,250 215,215 232,240 C240,265 240,300 238,325 Z" fill="#9a9aa0"/>',
         '<path d="M272,326 C300,255 292,220 274,240 C266,262 262,298 262,322 Z" fill="#8e8e94"/>',
         '<circle cx="236" cy="352" r="6" fill="#111"/><circle cx="264" cy="352" r="6" fill="#111"/>',
         '<path d="M244,372 L250,378 L256,372" stroke="#3a2a2a" stroke-width="3" fill="none"/>',
         # Arme um den Hasen
         '<path d="M160,300 C150,380 190,430 240,440" stroke="#d6b01e" stroke-width="40" fill="none" stroke-linecap="round"/>',
         '<path d="M340,300 C350,380 310,430 260,440" stroke="#c49e16" stroke-width="40" fill="none" stroke-linecap="round"/>',
         '<circle cx="236" cy="440" r="15" fill="#e2c6b6"/><circle cx="264" cy="440" r="15" fill="#d6b8a8"/>',
         # Kopf mit Kapuze
         '<path d="M170,180 C165,95 210,55 250,55 C290,55 335,95 330,180 C325,230 290,260 250,262 C210,260 175,230 170,180 Z" fill="url(#mc2)"/>',
         '<path d="M195,175 C195,120 222,95 250,95 C278,95 305,120 305,175 C305,215 280,240 250,242 C220,240 195,215 195,175 Z" fill="#2c2104"/>',
         '<ellipse cx="250" cy="180" rx="44" ry="52" fill="#e7cfc2"/>',
         '<path d="M206,165 C215,125 270,118 294,165 C270,150 240,148 206,165 Z" fill="#1c1410"/>',
         '<circle cx="234" cy="182" r="7" fill="#1a100c"/><circle cx="266" cy="182" r="7" fill="#1a100c"/>',
         '<circle cx="236" cy="180" r="2" fill="#fff"/><circle cx="268" cy="180" r="2" fill="#fff"/>',
         '<path d="M240,210 Q250,216 260,210" stroke="#8a4448" stroke-width="3" fill="none"/>',
         '<path d="M210,160 C205,200 208,225 215,240 M290,160 C295,200 292,225 285,240" stroke="#1c1410" stroke-width="7" fill="none"/>']
    return svg(500, 700, "".join(b), defs)


def rabbit():
    b = ['<ellipse cx="150" cy="215" rx="110" ry="14" fill="#000" opacity="0.5" filter="url(#b6)"/>',
         '<ellipse cx="160" cy="175" rx="80" ry="42" fill="#8a8a90"/>',
         '<ellipse cx="80" cy="160" rx="44" ry="40" fill="#96969c"/>',
         '<path d="M70,130 C40,70 10,60 20,90 C30,115 50,130 66,140 Z" fill="#96969c"/>',
         '<path d="M92,126 C90,60 70,40 66,70 C64,95 74,118 86,132 Z" fill="#8a8a90"/>',
         '<path d="M60,155 l10,10 M70,155 l-10,10" stroke="#111" stroke-width="3"/>',
         '<circle cx="96" cy="158" r="6" fill="#111"/>',
         '<path d="M150,140 L160,200" stroke="#5a5a60" stroke-width="2" stroke-dasharray="6,5"/>',
         '<path d="M200,190 l20,5" stroke="#6a1a1a" stroke-width="5" opacity="0.6"/>']
    return svg(300, 240, "".join(b))


# =====================================================================
#  DAS DING
# =====================================================================
def creature(fingers=0, sil=False):
    coat = "#c9a516" if not sil else "#0a0a0c"
    coatd = "#7a6208" if not sil else "#050506"
    skin = "#9c9a94" if not sil else "#0c0c0e"
    b = ['<ellipse cx="300" cy="1585" rx="130" ry="14" fill="#000" opacity="0.6" filter="url(#b6)"/>',
         # Beine
         f'<path d="M262,860 C255,1100 250,1350 240,1560 L262,1570 C278,1350 288,1100 292,870 Z" fill="{skin}"/>',
         f'<path d="M330,860 C342,1100 352,1350 368,1560 L346,1570 C328,1350 316,1100 308,870 Z" fill="{skin}"/>',
         f'<path d="M262,860 C255,1100 250,1350 240,1560" stroke="#000" stroke-width="3" opacity="0.4" fill="none"/>',
         # Mantel (zu klein, zerrissen)
         f'<path d="M200,280 C230,240 370,240 400,280 L425,820 L400,800 L385,850 L360,815 L335,870 L310,820 L285,860 L262,812 L238,850 L215,805 L178,830 Z" fill="{coat}"/>',
         f'<path d="M300,262 L300,860" stroke="{coatd}" stroke-width="5"/>',
         f'<path d="M215,300 C205,500 215,700 225,800" stroke="{coatd}" stroke-width="6" fill="none" opacity="0.6"/>']
    # Arme (sehr lang)
    for side, sx in ((-1, 205), (1, 395)):
        ex = sx + side * 40
        b.append(f'<path d="M{sx},300 C{sx + side * 50},450 {ex},700 {ex + side * 10},860" stroke="{coatd}" stroke-width="48" fill="none" stroke-linecap="round"/>')
        b.append(f'<path d="M{sx},300 C{sx + side * 50},450 {ex},700 {ex + side * 10},860" stroke="{coat}" stroke-width="36" fill="none" stroke-linecap="round"/>')
        b.append(f'<path d="M{ex + side * 8},840 C{ex + side * 18},960 {ex + side * 20},1060 {ex + side * 16},1150" stroke="{skin}" stroke-width="20" fill="none" stroke-linecap="round"/>')
        hx, hy = ex + side * 16, 1150
        for k in range(5):
            ang = (k - 2) * 0.16 + (0.12 * side if fingers else 0) * (1 if k % 2 else -1)
            import math
            l = 95 + (k == 2) * 20
            x2 = hx + math.sin(ang) * l * side * 0.6 + (k - 2) * 7
            y2 = hy + math.cos(ang) * l
            b.append(f'<path d="M{hx + (k - 2) * 5},{hy} Q{(hx + x2) / 2 + side * 6},{(hy + y2) / 2} {x2},{y2}" stroke="{skin}" stroke-width="7" fill="none" stroke-linecap="round"/>')
    # Hals + Kopf (geneigt)
    b.append(f'<path d="M290,280 C285,230 300,200 320,170 L340,180 C322,210 312,240 312,282 Z" fill="{skin}"/>')
    head = []
    head.append(f'<path d="M232,170 C222,60 282,10 335,12 C388,14 440,66 428,175 C422,240 380,275 330,277 C282,275 240,238 232,170 Z" fill="{coat}"/>')
    head.append('<path d="M260,170 C255,95 295,58 332,58 C369,58 408,95 402,170 C398,226 368,254 330,256 C294,254 264,226 260,170 Z" fill="#050403"/>')
    if not sil:
        head.append('<path d="M286,150 C286,100 308,80 331,80 C354,80 378,100 378,150 C378,205 356,240 331,244 C306,240 286,205 286,150 Z" fill="#c9c4b8"/>')
        head.append('<ellipse cx="312" cy="140" rx="15" ry="21" fill="#000" filter="url(#b2)"/><ellipse cx="352" cy="140" rx="15" ry="21" fill="#000" filter="url(#b2)"/>')
        head.append('<circle cx="314" cy="136" r="2.5" fill="#fff" opacity="0.8"/><circle cx="354" cy="136" r="2.5" fill="#fff" opacity="0.8"/>')
        head.append('<path d="M300,168 L304,190 M362,168 L358,190" stroke="#7a756a" stroke-width="2" opacity="0.6"/>')
        head.append('<path d="M290,200 Q331,232 372,200 Q331,216 290,200 Z" fill="#080606"/>')
        for i in range(9):
            x = 298 + i * 8.2
            y = 203 + 0.012 * (x - 331) ** 2 * -0.5 + 6
            head.append(f'<path d="M{x},{y - 4} l3,8 l3,-8" stroke="#e8e2d0" stroke-width="2" fill="none"/>')
    else:
        head.append('<circle cx="312" cy="145" r="3" fill="#bbb" opacity="0.6"/><circle cx="350" cy="145" r="3" fill="#bbb" opacity="0.6"/>')
    b.append(f'<g transform="rotate(-32 330 200)">{"".join(head)}</g>')
    return svg(600, 1600, "".join(b))


# =====================================================================
#  HINTERGRÜNDE
# =====================================================================
def exterior(sign_on=True):
    W, H = 1188, 2112
    defs = """
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#03050a"/><stop offset="1" stop-color="#16202e"/></linearGradient>
    <linearGradient id="fac" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a1e27"/><stop offset="1" stop-color="#0c0e13"/></linearGradient>
    <linearGradient id="gnd" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c0f15"/><stop offset="1" stop-color="#040507"/></linearGradient>
    <linearGradient id="ent" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2c4a4a"/><stop offset="1" stop-color="#0e1a1a"/></linearGradient>
    <filter id="neon" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9" result="g"/>
      <feMerge><feMergeNode in="g"/><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    """
    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']
    b.append('<ellipse cx="300" cy="300" rx="420" ry="90" fill="#2a3446" opacity="0.35" filter="url(#b30)"/>')
    b.append('<ellipse cx="900" cy="450" rx="380" ry="70" fill="#253042" opacity="0.3" filter="url(#b30)"/>')
    # Bäume
    for x in (-40, 70, 1080, 1180):
        b.append(f'<ellipse cx="{x}" cy="1300" rx="140" ry="300" fill="#05070a"/>')
    # Gebäude
    b.append('<rect x="-20" y="760" width="1228" height="760" fill="url(#fac)"/>')
    b.append('<rect x="-20" y="740" width="1228" height="30" fill="#232836"/>')
    for row in range(3):
        for col in range(9):
            x, y = 30 + col * 128, 980 + row * 70
            lit = (row, col) == (0, 7)
            fill = "#5c4a2a" if lit else "#090b10"
            b.append(f'<rect x="{x}" y="{y}" width="96" height="44" fill="{fill}" stroke="#20242e" stroke-width="3"/>')
            if lit:
                b.append(f'<rect x="{x + 40}" y="{y + 6}" width="14" height="38" fill="#0a0806"/>'
                         f'<ellipse cx="{x + 47}" cy="{y + 8}" rx="8" ry="9" fill="#0a0806"/>')
    # Eingang
    b.append('<rect x="380" y="1180" width="428" height="340" fill="url(#ent)"/>')
    for x in (380, 487, 594, 701, 808):
        b.append(f'<rect x="{x - 6}" y="1180" width="12" height="340" fill="#1a1f28"/>')
    b.append('<path d="M330,1130 L858,1130 L900,1180 L288,1180 Z" fill="#14171f"/>')
    b.append('<rect x="288" y="1176" width="612" height="10" fill="#0a0c10"/>')
    b.append('<ellipse cx="594" cy="1190" rx="230" ry="18" fill="#bfe8e0" opacity="0.25" filter="url(#b14)"/>')
    # Leuchtschrift
    spans = []
    for i, ch in enumerate("LINDENHOF"):
        broken = (i == 7 and not sign_on) or i == 4
        spans.append(f'<tspan fill="{"#3a0a10" if broken else "#ff2d48"}">{ch}</tspan>')
    b.append('<text x="594" y="900" font-family="DejaVu Sans, Arial" font-weight="bold" font-size="122" '
             f'letter-spacing="10" text-anchor="middle" filter="url(#neon)">{"".join(spans)}</text>')
    # Boden + Spiegelungen
    b.append(f'<rect x="0" y="1520" width="{W}" height="{H - 1520}" fill="url(#gnd)"/>')
    b.append('<rect x="150" y="1530" width="900" height="330" fill="#ff2d48" opacity="0.10" filter="url(#b30)"/>')
    for i in range(9):
        x = 140 + i * 107
        if i == 4 or (i == 7 and not sign_on):
            continue
        b.append(f'<rect x="{x}" y="1540" width="50" height="{260 + (i % 3) * 40}" fill="#ff2d48" opacity="0.18" filter="url(#b14)"/>')
    b.append('<rect x="420" y="1530" width="350" height="200" fill="#9fd8d0" opacity="0.08" filter="url(#b30)"/>')
    for i in range(7):
        x0 = 100 + i * 170
        b.append(f'<path d="M{x0},1560 L{x0 + (x0 - 594) * 1.6},{H}" stroke="#8a8a80" stroke-width="5" opacity="0.18"/>')
    for (x, y, rx) in ((300, 1700, 160), (820, 1820, 220), (520, 1950, 260)):
        b.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="22" fill="#1c2636" opacity="0.6"/>')
    # Laterne
    b.append('<rect x="1010" y="1080" width="12" height="470" fill="#0c0d10"/><path d="M990,1080 L1060,1080 L1050,1100 L1000,1100 Z" fill="#0c0d10"/>')
    b.append('<ellipse cx="1025" cy="1105" rx="40" ry="16" fill="#ffb060" filter="url(#b6)"/>')
    b.append('<path d="M1000,1105 L860,1560 L1200,1560 L1050,1105 Z" fill="#ffb060" opacity="0.07" filter="url(#b14)"/>')
    # Jonas klein, von hinten, läuft zum Eingang
    b.append('<g transform="translate(565,1530)"><ellipse cx="30" cy="125" rx="40" ry="6" fill="#000" opacity="0.6"/>'
             '<path d="M10,40 C15,25 45,25 50,40 L56,95 L4,95 Z" fill="#0c0e13"/><rect x="12" y="92" width="14" height="32" fill="#08090c"/>'
             '<rect x="34" y="92" width="14" height="32" fill="#08090c"/><circle cx="30" cy="22" r="15" fill="#140e0a"/>'
             '<path d="M8,50 L18,52" stroke="#9aa2ad" stroke-width="4" opacity="0.5"/></g>')
    return svg(W, H, "".join(b), defs)


def escalator():
    W, H = 1188, 2112
    defs = """
    <linearGradient id="ebg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a0d12"/><stop offset="1" stop-color="#05060a"/></linearGradient>
    <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5a7080" stop-opacity="0.25"/><stop offset="1" stop-color="#1a2028" stop-opacity="0.15"/></linearGradient>
    <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9fb8d0" stop-opacity="0.22"/><stop offset="1" stop-color="#9fb8d0" stop-opacity="0"/></linearGradient>
    """
    b = [f'<rect width="{W}" height="{H}" fill="url(#ebg)"/>']
    # Obere Galerie mit Läden
    b.append('<rect x="0" y="260" width="1188" height="420" fill="#0d1016"/>')
    for i in range(5):
        x = 20 + i * 240
        b.append(f'<rect x="{x}" y="320" width="200" height="300" fill="#07090d" stroke="#1a1e26" stroke-width="4"/>')
        for y in range(330, 620, 22):
            b.append(f'<line x1="{x + 6}" y1="{y}" x2="{x + 194}" y2="{y}" stroke="#151922" stroke-width="3"/>')
    b.append('<rect x="0" y="680" width="1188" height="26" fill="#1e232c"/>')
    b.append('<rect x="0" y="706" width="1188" height="110" fill="url(#glass)"/>')
    b.append('<rect x="0" y="702" width="1188" height="8" fill="#3a4250"/>')
    # Oberlicht-Strahlen
    b.append('<path d="M700,0 L860,0 L1188,900 L900,900 Z" fill="url(#beam)"/>')
    b.append('<path d="M300,0 L380,0 L560,900 L420,900 Z" fill="url(#beam)" opacity="0.6"/>')
    # Notausgang
    b.append('<rect x="980" y="180" width="140" height="56" fill="#0a3a1a"/><rect x="984" y="184" width="132" height="48" fill="#1fd06a" opacity="0.85"/>'
             '<text x="1050" y="218" font-family="DejaVu Sans" font-weight="bold" font-size="26" text-anchor="middle" fill="#03200e">AUSGANG</text>'
             '<ellipse cx="1050" cy="210" rx="120" ry="60" fill="#1fd06a" opacity="0.2" filter="url(#b30)"/>')
    # Boden unten
    b.append(f'<rect x="0" y="1900" width="{W}" height="{H - 1900}" fill="#0b0d11"/>')
    # Rolltreppe: von unten links nach oben rechts
    x0, y0, x1, y1 = 60, 1980, 1050, 760
    # Seitenwand hinten
    b.append(f'<path d="M{x0 + 120},{y0 - 260} L{x1 + 80},{y1 - 220} L{x1 + 140},{y1 - 120} L{x0 + 180},{y0 - 160} Z" fill="#141820"/>')
    # Stufen
    n = 26
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        ax, ay = x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0
        bx, by = x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1
        b.append(f'<path d="M{ax + 60},{ay - 100} L{ax + 260},{ay - 100} L{ax + 260},{by - 100} L{ax + 60},{by - 100} Z" fill="#1d2129"/>')
        b.append(f'<path d="M{ax + 60},{by - 100} L{bx + 60},{by - 100} L{bx + 260},{by - 100} L{ax + 260},{by - 100} Z" fill="#2a2f39"/>')
        b.append(f'<line x1="{ax + 60}" y1="{by - 100}" x2="{ax + 260}" y2="{by - 100}" stroke="#c8a830" stroke-width="3" opacity="0.5"/>')
    # Balustraden (Glas) + Handläufe
    for off, op in ((0, 1.0), (260, 0.9)):
        b.append(f'<path d="M{x0 + off},{y0 - 60} L{x1 + off},{y1 - 60} L{x1 + off},{y1 - 230} L{x0 + off},{y0 - 230} Z" fill="url(#glass)"/>')
        b.append(f'<path d="M{x0 + off},{y0 - 236} L{x1 + off},{y1 - 236}" stroke="#050506" stroke-width="22" stroke-linecap="round" opacity="{op}"/>')
        b.append(f'<path d="M{x0 + off},{y0 - 244} L{x1 + off},{y1 - 244}" stroke="#3a3f4a" stroke-width="3" opacity="{op}"/>')
        b.append(f'<path d="M{x0 + off},{y0 - 55} L{x1 + off},{y1 - 55}" stroke="#4a505c" stroke-width="10"/>')
    b.append(f'<path d="M{x0 + 260},{y0 - 50} L{x1 + 260},{y1 - 50} L{x1 + 260},{y1 + 40} L{x0 + 260},{y0 + 40} Z" fill="#20252e"/>')
    b.append('<text x="300" y="1840" font-family="DejaVu Sans" font-size="30" fill="#5a606a" transform="rotate(-50 300 1840)">AUSSER BETRIEB</text>')
    return svg(W, H, "".join(b), defs)


# =====================================================================
#  BUILD
# =====================================================================
def jobs():
    J = []

    def add(name, s, w, h):
        J.append((name, s, w, h))

    for e in ("open", "closed", "black", "serious"):
        for m in ("0", "1", "2", "grin"):
            if m == "grin" and e not in ("open", "black"):
                continue
            add(f"walter_{e}_{m}", walter(e, m), 900, 1100)
            add(f"walterwet_{e}_{m}", walter(e, m, wet=True), 900, 1100)
    for e in ("open", "wide", "closed"):
        for m in ("0", "1", "2"):
            add(f"jonas_{e}_{m}", jonas(e, m), 900, 1100)
    for e in ("open", "closed", "black"):
        for m in ("0", "1", "2", "grin"):
            add(f"mia_{e}_{m}", mia(e, m), 900, 1100)
    add("mia_sitting", mia_sitting(), 500, 700)
    add("rabbit", rabbit(), 300, 240)
    add("creature_0", creature(0), 600, 1600)
    add("creature_1", creature(1), 600, 1600)
    add("creature_sil", creature(0, sil=True), 600, 1600)
    add("walter_back", walter_back(), 400, 900)
    add("jonas_back", jonas_back(), 1000, 900)
    add("exterior_on", exterior(True), 1188, 2112)
    add("exterior_off", exterior(False), 1188, 2112)
    add("escalator", escalator(), 1188, 2112)
    return J


def build(force=False):
    todo = []
    for name, s, w, h in jobs():
        p_svg = os.path.join(ART, name + ".svg")
        p_png = os.path.join(ART, name + ".png")
        old = open(p_svg).read() if os.path.exists(p_svg) else None
        if force or old != s or not os.path.exists(p_png):
            open(p_svg, "w").write(s)
            todo.append(dict(svg=p_svg, png=p_png, w=w, h=h))
    if todo:
        jf = os.path.join(ART, "jobs.json")
        json.dump(todo, open(jf, "w"))
        subprocess.run(["node", os.path.join(ROOT, "svg2png.js"), jf], check=True)
    print(f"art: {len(todo)} PNGs gerendert")


if __name__ == "__main__":
    build()
