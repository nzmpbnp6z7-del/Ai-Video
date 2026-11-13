# -*- coding: utf-8 -*-
"""Drehbuch: Die Regeln des Nachtwächters.

Jedes Segment:
  scene  : Hintergrund-Szene
  say    : gesprochener Text (TTS)  -> wird auch als Untertitel gezeigt
  cap    : optional abweichender Untertitel (z.B. Ziffern statt ausgeschriebener Zahlen)
  voice  : narr | call | phone | man
  time   : Uhrzeit im HUD ab diesem Segment ("HH:MM")
  choice : (A-Text, B-Text) -> Entscheidungs-Karte mit Countdown
  sfx    : [(name, offset_s), ...]
  pad    : Pause nach dem Text (s)
  flick  : Stärke Lichtflackern 0..1
"""

TITLE = "DIE REGELN DES NACHTWÄCHTERS"

# (Text auf dem Zettel, gesprochener Text)
RULES = [
    ("Dienst: 22:00 – 6:00 Uhr. Verlasse das Gebäude NIE vor 6:00 Uhr – egal, wer dich darum bittet.",
     "Regel eins. Dein Dienst geht von zweiundzwanzig bis sechs Uhr. Verlasse das Gebäude nie vor sechs Uhr. Egal, wer dich darum bittet."),
    ("Das Radio im Wachraum darf nie ausgehen. Hörst du etwas, das du nicht hören willst: LAUTER drehen.",
     "Regel zwei. Das Radio im Wachraum darf niemals ausgehen. Hörst du etwas, das du nicht hören willst: Dreh es lauter."),
    ("Niemand, der hier nachts arbeitet, kennt deinen Namen. Für uns bist du nur „der Neue“.",
     "Regel drei. Niemand, der hier nachts arbeitet, kennt deinen Namen. Für uns bist du nur: der Neue."),
    ("Die Puppen bei Mode Kessler schauen immer zur Wand. Dreh ihnen NIE den Rücken zu.",
     "Regel vier. Die Schaufensterpuppen bei Mode Kessler schauen immer zur Wand. Dreh ihnen niemals den Rücken zu."),
    ("Dein Chef, Hr. Brandt, telefoniert nie. Er schreibt nur E-Mails.",
     "Regel fünf. Dein Chef, Herr Brandt, telefoniert nie. Er schreibt nur E-Mails."),
    ("Im Foodcourt stehen 24 Tische. Zähl sie niemals nach.",
     "Regel sechs. Im Foodcourt stehen vierundzwanzig Tische. Zähl sie niemals nach."),
    ("Es gibt nur 3 Lager. Siehst du eine Tür mit der Nr. 4: Geh weiter.",
     "Regel sieben. Es gibt nur drei Lager. Siehst du eine Tür mit der Nummer vier: Geh weiter."),
]
RULE8 = "8. Geh niemals in Lager 4. Du hast es versprochen."

END_HINT = "Schreib A oder B in die Kommentare. Die Lösung steckt in den Regeln."


def rule_caption(i):
    return f"Regel {i + 1}: " + RULES[i][0]


PARTS = []

# ---------------------------------------------------------------- TEIL 1
p1 = [
    dict(scene="corridor", time="21:54", say="Ich heiße Jonas. Gestern habe ich einen Nachtjob angenommen.", sfx=[("footsteps", 0.3)]),
    dict(scene="corridor", say="Wachmann im Einkaufszentrum Lindenhof. Nachts. Ganz allein.", flick=0.3),
    dict(scene="office", say="Im Wachraum lag ein Zettel. Handgeschrieben.", sfx=[("paper", 0.4)]),
    dict(scene="note:0", say="Mach jetzt einen Screenshot. Du wirst diese Regeln brauchen.", pad=0.6),
]
for i in range(7):
    p1.append(dict(scene=f"note:{i + 1}:{i}", say=RULES[i][1], cap=rule_caption(i), pad=0.4))
p1 += [
    dict(scene="note:7", say="Okay. Klingt seltsam. Aber ich brauchte das Geld.", pad=0.5),
    dict(scene="office", time="01:09", say="Die ersten Stunden waren ruhig. Das Radio rauschte leise vor sich hin.", radio=0.5),
    dict(scene="door3", time="01:12", say="Dann, um ein Uhr zwölf, hörte ich etwas aus Lager drei.",
         cap="Dann, um 01:12 Uhr, hörte ich etwas aus Lager 3.", radio=0.25),
    dict(scene="door3", voice="call", say="Jonas. Jonas. Komm her. Ich brauche Hilfe.", sfx=[("sting", 0.0)], flick=0.6, pad=0.8),
    dict(scene="door3", choice=("Hingehen", "Radio lauter drehen"),
         say="Was soll ich tun? A: Hingehen. Oder B: Das Radio lauter drehen."),
    dict(scene="door3", say=END_HINT, pad=1.2, end=True),
]
PARTS.append(dict(n=1, segs=p1))

# ---------------------------------------------------------------- TEIL 2
p2 = [
    dict(scene="door3", time="01:12", say="Die Stimme aus Lager drei rief meinen Namen.", cap="Die Stimme aus Lager 3 rief meinen Namen.", flick=0.4),
    dict(scene="note:7:2", say="Die richtige Antwort war B. Regel drei: Niemand hier kennt meinen Namen.", cap="Die richtige Antwort war B. Regel 3: Niemand hier kennt meinen Namen.", pad=0.4),
    dict(scene="note:7:1", say="Und Regel zwei: Hörst du etwas, das du nicht hören willst, dreh das Radio lauter.", cap="Und Regel 2: Hörst du etwas, das du nicht hören willst – dreh das Radio lauter.", pad=0.4),
    dict(scene="office", say="Ich drehte das Radio voll auf. Das Rufen wurde leiser. Dann hörte es auf.", radio=1.0),
    dict(scene="door3", say="Später fiel mir auf: Lager drei war von außen abgeschlossen. Den einzigen Schlüssel hatte ich.",
         cap="Später fiel mir auf: Lager 3 war von außen abgeschlossen. Den einzigen Schlüssel hatte ich.", radio=0.3, pad=0.6),
    dict(scene="corridor", time="02:40", say="Um zwei Uhr vierzig machte ich meine Runde. Erstes Obergeschoss.", cap="Um 02:40 Uhr machte ich meine Runde. Erstes Obergeschoss.", sfx=[("footsteps", 0.2)]),
    dict(scene="mann_n", say="Bei Mode Kessler standen die Puppen wie immer da. Gesicht zur Wand.", flick=0.2),
    dict(scene="mann_t", say="Dann flackerte meine Taschenlampe. Und eine von ihnen sah mich an.", sfx=[("sting", 1.8)], flick=1.0, pad=0.8),
    dict(scene="mann_t", choice=("Umdrehen & zum Wachraum rennen", "Anleuchten & langsam rückwärts weggehen"),
         say="Was soll ich tun? A: Umdrehen und zum Wachraum rennen. Oder B: Sie anleuchten und langsam rückwärts weggehen.", flick=0.4),
    dict(scene="mann_t", say=END_HINT, pad=1.2, end=True, flick=0.4),
]
PARTS.append(dict(n=2, segs=p2))

# ---------------------------------------------------------------- TEIL 3
p3 = [
    dict(scene="mann_t", time="02:41", say="Die Puppe bei Mode Kessler hatte mich angesehen.", flick=0.6),
    dict(scene="note:7:3", say="Die Antwort war B. Regel vier: Dreh ihnen niemals den Rücken zu.", cap="Die Antwort war B. Regel 4: Dreh ihnen NIE den Rücken zu.", pad=0.4),
    dict(scene="mann_t", say="Ich ließ das Licht auf ihr. Schritt für Schritt rückwärts. Sie bewegte sich nicht. Solange ich hinsah.", flick=0.3, sfx=[("footsteps_slow", 1.6)]),
    dict(scene="corridor", say="Als ich um die Ecke war, fiel hinter mir etwas um.", sfx=[("thud", 2.3)], pad=0.8),
    dict(scene="office", time="03:33", say="Zurück im Wachraum. Drei Uhr dreiunddreißig. Das Telefon klingelte.", cap="Zurück im Wachraum. 03:33 Uhr. Das Telefon klingelte.", sfx=[("ring", 2.6)], radio=0.3, pad=1.2),
    dict(scene="phone", voice="phone", say="Hier Brandt. Im Parkdeck brennt es. Raus aus dem Gebäude, sofort!", shake=True, radio=0.2),
    dict(scene="phone", say="Die Stimme klang genau wie mein Chef.", radio=0.2),
    dict(scene="phone", choice=("Sofort raus aus dem Gebäude", "Auflegen & im Wachraum bleiben"),
         say="Was soll ich tun? A: Sofort raus aus dem Gebäude. Oder B: Auflegen und im Wachraum bleiben.", radio=0.2),
    dict(scene="phone", say=END_HINT, pad=1.2, end=True, radio=0.2),
]
PARTS.append(dict(n=3, segs=p3))

# ---------------------------------------------------------------- TEIL 4
p4 = [
    dict(scene="phone", time="03:34", say="Mein Chef rief an. Angeblich brannte es.", radio=0.2),
    dict(scene="note:7:4", say="Die Antwort war B. Regel fünf: Herr Brandt telefoniert nie.", cap="Die Antwort war B. Regel 5: Herr Brandt telefoniert nie.", pad=0.3),
    dict(scene="note:7:0", say="Und Regel eins: Verlasse das Gebäude nie vor sechs Uhr. Egal, wer dich darum bittet.", cap="Und Regel 1: Verlasse das Gebäude NIE vor 6:00 Uhr – egal, wer dich darum bittet.", pad=0.4),
    dict(scene="phone", say="Ich legte auf. Kein Rauch. Kein Alarm. Nur das Rauschen vom Radio.", radio=0.5),
    dict(scene="phone", say="Das Telefon klingelte noch dreimal. Dann nie wieder.", sfx=[("ring", 2.4)], radio=0.3, shake=True, pad=0.8),
    dict(scene="entrance", time="05:41", say="Fünf Uhr einundvierzig. Fast geschafft. Da ging die Glastür am Haupteingang auf.", cap="05:41 Uhr. Fast geschafft. Da ging die Glastür am Haupteingang auf.", sfx=[("door", 3.6)], pad=0.6),
    dict(scene="entrance_man", say="Ein Mann in Uniform. Die Taschenlampe direkt auf mich gerichtet.", flick=0.3),
    dict(scene="entrance_man", voice="man", say="Morgen, Jonas. Schichtwechsel. Du kannst heute früher gehen.", pad=0.6),
    dict(scene="entrance_man", choice=("Nach Hause gehen", "Bis 6:00 Uhr bleiben"),
         say="Was soll ich tun? A: Nach Hause gehen. Oder B: Bis sechs Uhr bleiben. Tipp: Es gibt zwei Hinweise.",
         hint="Tipp: In den Regeln stecken ZWEI Hinweise."),
    dict(scene="entrance_man", say=END_HINT, pad=1.2, end=True),
]
PARTS.append(dict(n=4, segs=p4))

# ---------------------------------------------------------------- TEIL 5 (Finale)
p5 = [
    dict(scene="entrance_man", time="05:42", say="Der Mann am Eingang wollte, dass ich früher gehe."),
    dict(scene="note:7:0", say="Die Antwort war B. Regel eins: Nie vor sechs Uhr gehen.", cap="Die Antwort war B. Regel 1: NIE vor 6:00 Uhr gehen.", pad=0.3),
    dict(scene="note:7:2", say="Und er nannte mich Jonas. Aber hier kennt niemand meinen Namen.", pad=0.4),
    dict(scene="entrance_man", say="Ich blieb stehen. Er lächelte. Viel zu lange.", flick=0.5, pad=0.4),
    dict(scene="entrance", say="Dann ging die Tür wieder zu. Und er war weg.", sfx=[("door", 0.4)], pad=0.6),
    dict(scene="entrance", time="06:00", say="Um Punkt sechs kam die Frühschicht. Ein alter Mann. Er nickte nur: Morgen, Neuer.",
         cap="Um Punkt 6:00 Uhr kam die Frühschicht. Ein alter Mann. Er nickte nur: „Morgen, Neuer.“"),
    dict(scene="office", say="Bevor ich ging, sah ich mir den Zettel noch einmal an.", sfx=[("paper", 0.5)]),
    dict(scene="note_final", say="Ganz unten stand eine neue Regel. Regel acht.", cap="Ganz unten stand eine neue Regel. Regel 8.", sfx=[("sting", 2.0)], pad=0.6),
    dict(scene="note_final", say="Geh niemals in Lager vier. Du hast es versprochen.", cap="„Geh niemals in Lager 4. Du hast es versprochen.“", pad=0.6),
    dict(scene="door4", say="Das Problem: Es war meine Handschrift. Und ich erinnere mich nicht, das geschrieben zu haben.", flick=0.5, pad=1.0),
    dict(scene="door4", say="Wie viele Antworten hattest du richtig? Schreib es in die Kommentare.", pad=1.5, end=True, final=True, flick=0.3),
]
PARTS.append(dict(n=5, segs=p5))
