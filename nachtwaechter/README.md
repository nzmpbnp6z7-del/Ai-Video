# Die Regeln des Nachtwächters – TikTok-Serie (5 Teile)

Interaktive Horror-Miniserie im Hochformat (1080×1920, 30 fps). Jonas fängt einen Nachtjob
im leeren Einkaufszentrum *Lindenhof* an und findet einen Zettel mit sieben seltsamen Regeln.
Jeder Teil endet mit einer A/B-Entscheidung – die richtige Antwort steckt in den Regeln aus Teil 1.
Der nächste Teil beginnt mit der Auflösung.

| Teil | Situation am Ende | Richtig | Versteckter Hinweis |
|---|---|---|---|
| 1 | Eine Stimme ruft aus Lager 3 „Jonas“ – A: hingehen, B: Radio lauter drehen | **B** | Regel 3 (niemand kennt deinen Namen) + Regel 2 (lauter drehen) |
| 2 | Eine Puppe bei Mode Kessler sieht dich an – A: umdrehen & rennen, B: anleuchten & rückwärts gehen | **B** | Regel 4 (nie den Rücken zudrehen) |
| 3 | 03:33 Uhr, „Herr Brandt“ ruft an: Feuer, sofort raus – A: raus, B: auflegen & bleiben | **B** | Regel 5 (Brandt telefoniert nie) + Regel 1 (nie vor 6 Uhr raus) |
| 4 | 05:41 Uhr, Mann in Uniform: „Morgen, Jonas. Du kannst früher gehen.“ – A: gehen, B: bis 6 Uhr bleiben | **B** | Regel 1 + Regel 3 (er kennt deinen Namen) |
| 5 | Finale: Auflösung + Twist (Regel 8 in Jonas' eigener Handschrift: „Geh niemals in Lager 4.“) | – | Regel 7 (es gibt nur 3 Lager) |

Regel 6 (Foodcourt-Tische) ist ein bewusster Red Herring bzw. Aufhänger für eine Fortsetzung.

## Dateien
- `story.py` – Drehbuch (Regeln, Segmente, Entscheidungen)
- `render.py` – Generator: Szenen (PIL), Stimme (espeak-ng + MBROLA de6/de4), Sounddesign (numpy), Untertitel, HUD, Ken-Burns, Grain/Flackern
- `output/nachtwaechter_teil1..5.mp4` – die fertigen Clips, `output/nachtwaechter_komplett.mp4` – alle Teile am Stück

## Neu rendern
```bash
apt-get install -y espeak-ng mbrola mbrola-de6 mbrola-de4 ffmpeg
pip install numpy pillow
python3 render.py          # alle Teile, oder z.B. python3 render.py 2 3
```

Tipp für den Upload: In der Caption von Teil 1 „Screenshot die Regeln!“ schreiben und die Teile als Playlist anlegen.
Die Stimme ist eine Offline-Sprachsynthese – für TikTok kann man die Spur auch durch eine eigene Aufnahme oder eine
KI-Stimme ersetzen (Texte stehen in `story.py`).
