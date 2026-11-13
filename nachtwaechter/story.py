# -*- coding: utf-8 -*-
"""Drehbuch: Die Regeln des Nachtwächters (Version 2).

Figuren
  Jonas  – 19, neuer Nachtwächter, Ich-Erzähler
  Walter – 68, alter Nachtwächter, seit 31 Jahren im Lindenhof
  Mama   – Jonas' Mutter (nur am Telefon)
  Mia    – kleines Mädchen im gelben Regenmantel … angeblich
  Das Ding – imitiert Stimmen, die es gehört hat

Segment-Felder
  shot   : Name der Einstellung (siehe render.py, SHOTS)
  who    : Sprecher (jonas | walter | walter_door | mama | mama_door | mia | mia_dark | creature)
  say    : gesprochener Text
  cap    : abweichender Untertitel
  talk   : True = Figur im Bild spricht (Lippen bewegen sich)
  time   : Uhrzeit im Kamera-HUD
  sfx    : [(name, offset)]
  pad    : Pause nach dem Text
  tense  : Spannungs-Level 0..1 (Musik, Herzschlag)
  opt    : beliebige Shot-Optionen
  choice : (A, B)  -> Entscheidungs-Karte mit Countdown
"""

TITLE = "DIE REGELN DES NACHTWÄCHTERS"

RULES = [
    "Hier drin kennt niemand deinen Namen. Halte es so.",
    "Das Radio übertönt alles, was nicht hier sein sollte.",
    "Was im Licht steht, kann sich nicht bewegen.",
    "Ich komme um 6 Uhr. Nie früher.",
]

END_Q = "Die Antwort steckt in Walters Regeln. Schreib A oder B in die Kommentare."

PARTS = []

# ===================================================================== TEIL 1
PARTS.append(dict(n=1, name="Die erste Nacht", segs=[
    dict(shot="hook", who="jonas", say="Diese vier Regeln haben mir in einer einzigen Nacht dreimal das Leben gerettet.",
         sfx=[("sting", 0.0)], tense=0.8, pad=0.3),
    dict(shot="exterior", who="jonas", time="21:47", say="Ich bin Jonas, neunzehn. Ich brauchte Geld. Also nahm ich den Job, den keiner wollte.",
         sfx=[("thunder", 0.4)], title=True, tense=0.2),
    dict(shot="exterior", who="jonas", say="Nachtwächter im Lindenhof. Einem Einkaufszentrum, das bald abgerissen wird.",
         opt=dict(push=True), tense=0.25, pad=0.2),
    dict(shot="walter", who="walter", talk=True, say="Du bist also der Neue.", tense=0.2, pad=0.4),
    dict(shot="walter", who="walter", talk=True, say="Nein. Sag mir nicht, wie du heißt. Ist besser so, Junge.", tense=0.25),
    dict(shot="walter", who="jonas", say="Das war Walter. Einunddreißig Jahre Nachtschicht. Seine Hände haben die ganze Zeit gezittert.",
         cap="Das war Walter. 31 Jahre Nachtschicht. Seine Hände haben die ganze Zeit gezittert.", opt=dict(close=True), tense=0.3),
    dict(shot="card", who="walter", say="Vier Regeln. Lern sie auswendig. Sie halten dich am Leben.",
         opt=dict(reveal=0), sfx=[("paper", 0.1)], tense=0.35),
    dict(shot="card", who="walter", say="Eins. Hier drin kennt niemand deinen Namen. Halte es so.", opt=dict(reveal=1, hl=0), tense=0.35, pad=0.4),
    dict(shot="card", who="walter", say="Zwei. Das Radio übertönt alles, was nicht hier sein sollte.", opt=dict(reveal=2, hl=1), tense=0.35, pad=0.4),
    dict(shot="card", who="walter", say="Drei. Was im Licht steht, kann sich nicht bewegen.", opt=dict(reveal=3, hl=2), tense=0.4, pad=0.4),
    dict(shot="card", who="walter", say="Vier. Ich komme um sechs. Nie früher.", opt=dict(reveal=4, hl=3), tense=0.4, pad=0.6),
    dict(shot="leave", who="walter", say="Ich bin um sechs zurück. Keine Minute früher.", sfx=[("door", 2.4), ("lock", 4.4)], pad=1.2, tense=0.3),
    dict(shot="corridor_jonas", who="jonas", time="00:12", say="Dann war ich allein. Vierzigtausend Quadratmeter Dunkelheit.",
         cap="Dann war ich allein. 40.000 Quadratmeter Dunkelheit.", sfx=[("footsteps", 0.2)], tense=0.35),
    dict(shot="phone_call", who="jonas", time="00:30", say="Um halb eins rief meine Mutter an. Und ich hab nicht nachgedacht.",
         sfx=[("buzz", 0.0), ("buzz", 1.6)], tense=0.4),
    dict(shot="phone_call", who="mama", say="Jonas? Schatz? Hast du was gegessen? Jonas, hörst du mich?", opt=dict(active=True), hall=True, tense=0.4),
    dict(shot="watcher", who="jonas", say="Ihre Stimme hallte durch das ganze Gebäude. Und ganz hinten im Gang hat sich etwas bewegt.",
         sfx=[("low_hit", 3.2)], tense=0.65, pad=0.8),
    dict(shot="jonas_office", who="jonas", time="01:12", say="Eine halbe Stunde später. Wachraum. Das Radio rauschte leise vor sich hin.",
         radio=0.4, tense=0.4, sfx=[("knock", 4.6)], pad=1.0),
    dict(shot="door3", who="mama_door", say="Jonas? Schatz, ich bin's. Mach bitte auf. Mir ist so kalt.",
         sfx=[("knock", 0.0)], radio=0.2, tense=0.75, pad=0.6, opt=dict(feet=True)),
    dict(shot="door3", who="jonas", say="Das war die Stimme meiner Mutter. Aus Lager drei. Das von außen abgeschlossen ist.",
         cap="Das war die Stimme meiner Mutter. Aus Lager 3. Das von außen abgeschlossen ist.", opt=dict(feet=True, push=True),
         radio=0.2, tense=0.85, sfx=[("knock", 3.0)]),
    dict(shot="door3", who="jonas", choice=("Zu Lager 3 gehen und aufmachen", "Das Radio lauter drehen"),
         say="Was soll ich tun? A: Hingehen und aufmachen. Oder B: Das Radio lauter drehen.", opt=dict(feet=True), radio=0.2, tense=1.0),
    dict(shot="door3", who="jonas", say=END_Q, end=True, pad=1.4, radio=0.2, tense=0.5),
]))

# ===================================================================== TEIL 2
PARTS.append(dict(n=2, name="Das Mädchen auf der Rolltreppe", segs=[
    dict(shot="door3", who="mama_door", say="Jonas? Mach bitte auf.", opt=dict(feet=True), title=True, sfx=[("knock", 0.2)], tense=0.7, pad=0.6),
    dict(shot="card", who="jonas", say="Richtig war B. Regel eins: Hier drin kennt niemand meinen Namen. Wer ihn trotzdem ruft, hat ihn nur aufgeschnappt.",
         cap="Richtig war B. Regel 1: Hier drin kennt niemand meinen Namen. Wer ihn trotzdem ruft, hat ihn nur aufgeschnappt.",
         opt=dict(reveal=4, hl=0), tense=0.4),
    dict(shot="card", who="jonas", say="Und Regel zwei: Das Radio übertönt alles, was nicht hier sein sollte.",
         cap="Und Regel 2: Das Radio übertönt alles, was nicht hier sein sollte.", opt=dict(reveal=4, hl=1), tense=0.4),
    dict(shot="radio", who="jonas", say="Ich drehte auf, bis die Boxen kratzten. Die Stimme wurde leiser. Und leiser.", radio=1.0, tense=0.6),
    dict(shot="radio", who="mama_door", say="Warum machst du nicht auf?", radio=1.0, gain=0.45, tense=0.6, pad=0.8),
    dict(shot="phone_msg", who="jonas", time="01:14", say="Eine Minute später bekam ich eine Nachricht.", sfx=[("buzz", 0.0)], radio=0.3, tense=0.4, pad=0.8),
    dict(shot="phone_msg", who="jonas", say="Meine Mutter lag die ganze Zeit zu Hause im Bett.", opt=dict(zoom=True), radio=0.3, tense=0.6, sfx=[("low_hit", 0.2)], pad=0.6),
    dict(shot="corridor_jonas", who="jonas", time="02:40", say="Um zwei Uhr vierzig machte ich meine Runde. Erste Etage. Da hörte ich jemanden summen.",
         cap="Um 02:40 Uhr machte ich meine Runde. Erste Etage. Da hörte ich jemanden summen.", sfx=[("footsteps", 0.2), ("hum", 4.2)], tense=0.45),
    dict(shot="escalator", who="jonas", say="Auf der stillstehenden Rolltreppe saß ein kleines Mädchen. Gelber Regenmantel. Nasse Gummistiefel.",
         sfx=[("hum", 0.0)], tense=0.5),
    dict(shot="mia", who="mia", talk=True, say="Ich hab mich versteckt, als alle nach Hause gegangen sind. Jetzt find ich meine Mama nicht mehr.", tense=0.5),
    dict(shot="jonas_close", who="jonas", say="Sie war vielleicht sieben. Ihre Stiefel tropften. Dabei hatte es seit Stunden aufgehört zu regnen.",
         sfx=[("drip", 0.5), ("drip", 2.1), ("drip", 3.4)], tense=0.6),
    dict(shot="mia", who="mia", talk=True, say="Ich heiße Mia. Und wie heißt du?", opt=dict(tilt=True), tense=0.8, pad=0.6),
    dict(shot="mia", who="jonas", choice=("„Ich heiße Jonas.“", "„Ich bin nur der Wachmann.“"),
         say="Was soll ich antworten? A: Ich heiße Jonas. Oder B: Ich bin nur der Wachmann.", opt=dict(tilt=True), tense=1.0),
    dict(shot="mia", who="jonas", say=END_Q, end=True, pad=1.4, opt=dict(tilt=True), tense=0.5),
]))

# ===================================================================== TEIL 3
PARTS.append(dict(n=3, name="Was im Licht steht", segs=[
    dict(shot="mia", who="mia", talk=True, say="Und wie heißt du?", opt=dict(tilt=True), title=True, tense=0.7, pad=0.6),
    dict(shot="card", who="jonas", say="Richtig war B. Regel eins: Hier drin kennt niemand deinen Namen. Halte es so.",
         cap="Richtig war B. Regel 1: Hier drin kennt niemand deinen Namen. Halte es so.", opt=dict(reveal=4, hl=0), tense=0.4),
    dict(shot="jonas_close", who="jonas", talk=True, say="Ich bin nur der Wachmann.", tense=0.6, pad=0.6),
    dict(shot="mia", who="jonas", say="Ihr Lächeln blieb einfach stehen. Wie eingefroren.", opt=dict(tilt=True, freeze=True), tense=0.75, pad=0.3),
    dict(shot="mia", who="mia_dark", talk=True, say="Schade.", opt=dict(dark=True), sfx=[("sting", 0.0)], tense=0.95, pad=1.0),
    dict(shot="blackout", who="jonas", say="Dann ging das Licht aus. Im ganzen Gebäude.", sfx=[("power_down", 0.0), ("click", 2.6)], tense=0.6, pad=0.6),
    dict(shot="escalator_empty", who="jonas", say="Die Rolltreppe war leer. Nur ihr Stoffhase lag noch da.", tense=0.6, pad=0.4),
    dict(shot="creature", who="jonas", say="Am Ende des Gangs stand etwas. Es trug ihren gelben Regenmantel. Aber es war fast drei Meter groß.",
         opt=dict(dist=1.0), tense=0.8, sfx=[("low_hit", 1.0)]),
    dict(shot="creature", who="jonas", say="Meine Taschenlampe flackerte. Und jedes Mal, wenn es dunkel wurde, war es näher.",
         opt=dict(dist=1.0, approach=True), tense=0.95),
    dict(shot="creature", who="jonas", choice=("Umdrehen und zum Wachraum rennen", "Licht draufhalten und rückwärts gehen"),
         say="Was soll ich tun? A: Umdrehen und rennen. Oder B: Das Licht draufhalten und rückwärts gehen.",
         hint="Es ist nur noch zehn Meter entfernt.", opt=dict(dist=0.45), tense=1.0),
    dict(shot="creature", who="jonas", say=END_Q, end=True, pad=1.4, opt=dict(dist=0.45), tense=0.5),
]))

# ===================================================================== TEIL 4
PARTS.append(dict(n=4, name="Klopfen an der Glastür", segs=[
    dict(shot="creature", who="jonas", say="Es kam näher. Jedes Mal, wenn das Licht ausging.", opt=dict(dist=0.45, approach=True), title=True, tense=0.9),
    dict(shot="card", who="jonas", say="Richtig war B. Regel drei: Was im Licht steht, kann sich nicht bewegen.",
         cap="Richtig war B. Regel 3: Was im Licht steht, kann sich nicht bewegen.", opt=dict(reveal=4, hl=2), tense=0.4),
    dict(shot="creature_close", who="jonas", say="Ich hielt den Strahl genau auf sein Gesicht. Es bewegte sich nicht. Nur seine Finger zuckten.", tense=0.9),
    dict(shot="creature", who="jonas", say="Ich ging rückwärts. Vierzig Meter. Ohne zu blinzeln. Bis ich die Tür vom Wachraum im Rücken spürte.",
         cap="Ich ging rückwärts. 40 Meter. Ohne zu blinzeln. Bis ich die Tür vom Wachraum im Rücken spürte.",
         opt=dict(dist=0.3, recede=True), sfx=[("slam", 6.6)], tense=0.85, pad=0.8),
    dict(shot="jonas_office", who="jonas", time="03:20", say="Den Rest der Nacht saß ich mit dem Rücken zur Wand. Das Radio auf voller Lautstärke.",
         opt=dict(scared=True), radio=0.9, tense=0.5),
    dict(shot="cctv", who="jonas", time="05:41", say="Um fünf Uhr einundvierzig klopfte jemand an die Glastür vom Haupteingang.",
         cap="Um 05:41 Uhr klopfte jemand an die Glastür vom Haupteingang.", sfx=[("glass_knock", 1.0), ("glass_knock", 3.4)], radio=0.4, tense=0.6),
    dict(shot="glass_walter", who="walter_door", talk=True, say="Jonas! Mach auf! Ich hab meinen Schlüssel vergessen!", sfx=[("glass_knock", 0.0)], tense=0.75),
    dict(shot="glass_walter", who="jonas", say="Es war Walter. Klatschnass. Er sah panisch aus.", opt=dict(panic=True), tense=0.75),
    dict(shot="glass_walter", who="walter_door", talk=True, say="Bitte, Jonas! Hier draußen ist irgendwas! Es kommt näher!", sfx=[("glass_knock", 0.0), ("glass_knock", 2.2)],
         opt=dict(shake=True), tense=0.9),
    dict(shot="glass_walter", who="jonas", choice=("Die Tür aufmachen", "Nicht aufmachen"),
         say="Was soll ich tun? A: Die Tür aufmachen. Oder B: Nicht aufmachen. Kleiner Tipp: Es gibt zwei Hinweise.",
         hint="Tipp: Es gibt ZWEI Hinweise.", tense=1.0),
    dict(shot="glass_walter", who="jonas", say=END_Q, end=True, pad=1.4, tense=0.5),
]))

# ===================================================================== TEIL 5
PARTS.append(dict(n=5, name="Sechs Uhr", segs=[
    dict(shot="glass_walter", who="walter_door", talk=True, say="Jonas! Mach auf!", title=True, sfx=[("glass_knock", 0.0)], tense=0.8, pad=0.6),
    dict(shot="card", who="jonas", say="Richtig war B. Regel vier: Ich komme um sechs. Nie früher.",
         cap="Richtig war B. Regel 4: Ich komme um 6 Uhr. Nie früher.", opt=dict(reveal=4, hl=3), tense=0.4),
    dict(shot="card", who="jonas", say="Und Walter kannte meinen Namen gar nicht. Er wollte ihn nie wissen.", opt=dict(reveal=4, hl=0), tense=0.5),
    dict(shot="glass_walter", who="jonas", say="Ich blieb einfach stehen. Walter hörte auf zu klopfen. Und lächelte. Immer breiter.",
         opt=dict(grin=True), tense=0.85),
    dict(shot="glass_walter", who="creature", talk=True, say="Morgen Nacht, Jonas.", opt=dict(grin=True, black=True, close=True),
         sfx=[("sting", 0.0)], tense=1.0, pad=1.0),
    dict(shot="entrance", who="jonas", say="Dann trat er zurück in den Regen. Und war verschwunden.", tense=0.5, pad=0.6),
    dict(shot="dawn", who="jonas", time="06:00", say="Um Punkt sechs ging die Sonne auf. Und Walter kam. Der echte. Trocken. Mit zwei Kaffee.",
         sfx=[("keys", 1.0), ("door", 2.5)], tense=0.15),
    dict(shot="walter_dawn", who="walter", talk=True, say="Na, Junge? Du lebst ja noch. Respekt.", tense=0.1),
    dict(shot="jonas_close", who="jonas", talk=True, say="Du warst vorhin schon mal hier. Um fünf Uhr einundvierzig.", opt=dict(dawn=True), tense=0.3),
    dict(shot="walter_dawn", who="walter", talk=True, say="Hast du aufgemacht?", opt=dict(serious=True), tense=0.5, pad=0.5),
    dict(shot="jonas_close", who="jonas", talk=True, say="Nein.", opt=dict(dawn=True), tense=0.5, pad=0.6),
    dict(shot="walter_dawn", who="walter", talk=True, say="Gut. Der Letzte hat aufgemacht.", opt=dict(serious=True), tense=0.6, pad=0.8),
    dict(shot="walter_dawn", who="walter", talk=True, say="Geh nach Hause und schlaf dich aus. Wir sehen uns heute Abend. Jonas.", tense=0.6, pad=0.4),
    dict(shot="walter_end", who="jonas", say="Er ging den Gang hinunter. Und mir wurde eiskalt. Denn ich hatte Walter nie gesagt, wie ich heiße.",
         sfx=[("sting", 5.2)], tense=0.9, pad=0.6),
    dict(shot="walter_end", who="jonas", say="Wie viele Antworten hattest du richtig? Schreib es in die Kommentare.", opt=dict(turn=True),
         end=True, final=True, pad=1.6, tense=0.4),
]))
