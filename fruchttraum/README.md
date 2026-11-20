# Mathestunde – ein Film in sehr schlechtem 3D

Apfel Kevin schläft im Matheunterricht ein, träumt von Schafen auf Drogen,
gerät in eine Schlafparalyse (Schatten-Schaf!) und wird von seinem Lehrer
Herrn Banane geweckt. Kein Ton, nur eingebrannte deutsche Untertitel.

- Video: `output/mathestunde.mp4` (1080×1920, ~83 s, 15 fps Animation)
- Neu rendern: `python3 film.py output/mathestunde.mp4`
- Vorschaubilder: `python3 film.py --preview 5 20 45`

Der Renderer (`engine.py`) ist absichtlich schlecht: Flat-Shading,
Maler-Algorithmus mit Sortierfehlern, Flächen verschwinden an der Near-Plane,
niedrige Auflösung mit grobem Hochskalieren. Figuren und Kulissen: `chars.py`,
Shots und Untertitel: `film.py`.
