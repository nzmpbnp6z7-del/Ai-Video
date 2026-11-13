# Die Regeln des Nachtwächters – TikTok-Horrorserie (5 Teile)

Interaktive Horror-Miniserie im Hochformat (1080×1920, 30 fps). Jeder Teil endet mit einer
A/B-Entscheidung mit Countdown. Die richtige Antwort steckt in Walters **vier Regeln** aus Teil 1.
Der nächste Teil beginnt mit der Auflösung.

## Figuren
| Figur | Rolle | Stimme |
|---|---|---|
| **Jonas** (19) | neuer Nachtwächter, Ich-Erzähler | Piper „thorsten“ |
| **Walter** (68) | alter Nachtwächter, will Jonas' Namen nicht wissen | Piper „karlsson“, tiefer gepitcht |
| **Mama** | ruft um 00:30 an und sagt laut „Jonas“ | Piper „kerstin“ (Telefonklang) |
| **Mia** | Mädchen im gelben Regenmantel auf der Rolltreppe | Piper „ramona“, hochgepitcht |
| **Das Ding** | imitiert jede Stimme, die es gehört hat | alle Stimmen übereinander, verzerrt |

## Die Regeln (Walters Karteikarte)
1. Hier drin kennt niemand deinen Namen. Halte es so.
2. Das Radio übertönt alles, was nicht hier sein sollte.
3. Was im Licht steht, kann sich nicht bewegen.
4. Ich komme um 6 Uhr. Nie früher.

## Folgen & Lösungen
| Teil | Situation am Ende | Richtig | Versteckter Hinweis |
|---|---|---|---|
| 1 – Die erste Nacht | „Mama“ ruft aus dem abgeschlossenen Lager 3: „Jonas, mach auf!“ – A: hingehen, B: Radio lauter | **B** | Regel 1 + 2 (das Ding hat den Namen nur beim Telefonat aufgeschnappt) |
| 2 – Das Mädchen auf der Rolltreppe | Mia fragt: „Und wie heißt du?“ – A: „Ich heiße Jonas“, B: „Ich bin nur der Wachmann“ | **B** | Regel 1 |
| 3 – Was im Licht steht | Das Ding im gelben Regenmantel kommt bei jedem Flackern näher – A: rennen, B: anleuchten & rückwärts gehen | **B** | Regel 3 |
| 4 – Klopfen an der Glastür | 05:41 Uhr, „Walter“ klopft: „Jonas! Mach auf!“ – A: aufmachen, B: nicht aufmachen | **B** | Regel 4 + Regel 1 (Walter kennt den Namen gar nicht) |
| 5 – Sechs Uhr (Finale) | Auflösung, der echte Walter kommt … und sagt zum Abschied „Jonas“ | – | Twist: Jonas hat Walter nie seinen Namen gesagt |

## Dateien
- `story.py` – Drehbuch (Regeln, Figuren, Segmente, Entscheidungen)
- `art.py` – SVG-Zeichnungen der Figuren (mit Augen-/Mund-Varianten für Blinzeln & Lippenbewegung) und neuer Hintergründe, gerendert per Chromium (`svg2png.js`)
- `scenes.py` – prozedurale Hintergründe (Gang, Wachraum, Lagertür, Haupteingang), Regelkarte, Handy-Bildschirme
- `voices.py` – Figurenstimmen (Piper, neuronale Offline-TTS) + Nachbearbeitung
- `sound.py` – Sounddesign: Spannungsmusik mit Herzschlag, Regen, Funkrauschen, Effekte
- `render.py` – Einstellungen (Shots), Kamera, Taschenlampen-Licht, Lip-Sync, Karaoke-Untertitel, Export
- `output/nachtwaechter_teil1..5.mp4` – fertige Clips

## Neu rendern
```bash
apt-get install -y ffmpeg
pip install numpy pillow piper-tts
./get_voices.sh            # lädt die deutschen Piper-Stimmen nach ./voices
python3 render.py          # alle Teile, oder z.B. python3 render.py 2 3
```
Benötigt Node.js mit Playwright/Chromium für das Rendern der SVG-Figuren.
