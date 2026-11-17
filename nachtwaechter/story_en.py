# -*- coding: utf-8 -*-
"""Script: The Night Watchman's Rules (English, voice: ElevenLabs "Roger").

Same structure as story.py. Additional field:
  tag : ElevenLabs v4 delivery tag(s) placed before the line
All lines are spoken by Roger; `who` controls caption colour, name tag and audio effect
(phone filter, muffled door, creature distortion).
"""

TITLE = "THE NIGHT WATCHMAN'S RULES"

RULES = [
    "Nobody in here knows your name. Keep it that way.",
    "The radio drowns out everything that shouldn't be here.",
    "Whatever stands in the light cannot move.",
    "I come back at 6 a.m. Never earlier.",
]

END_Q = "The answer is hidden in Walter's rules. Comment A or B."

PARTS = []

PARTS.append(dict(n=1, name="The First Night", segs=[
    dict(shot="hook", who="jonas", tag="[dramatically]", say="These four rules saved my life three times in a single night.",
         sfx=[("sting", 0.0)], tense=0.8),
    dict(shot="exterior", who="jonas", tag="[nervous]", time="21:47", title=True,
         say="My name is Jonas. I'm nineteen. I needed money, so I took the job nobody wanted.", sfx=[("thunder", 0.4)], tense=0.2),
    dict(shot="exterior", who="jonas", tag="[nervous]", say="Night watchman at Linden Mall. A shopping center that's about to be torn down.",
         opt=dict(push=True), tense=0.25),
    dict(shot="walter", who="walter", talk=True, tag="[elderly voice] [raspy]", say="So you're the new guy.", tense=0.2),
    dict(shot="walter", who="walter", talk=True, tag="[elderly voice] [raspy]", say="No. Don't tell me your name. It's better that way, kid.", tense=0.25),
    dict(shot="walter", who="jonas", tag="[softly]", say="That was Walter. Thirty-one years of night shifts. His hands never stopped shaking.",
         opt=dict(close=True), tense=0.3),
    dict(shot="card", who="walter", tag="[elderly voice] [raspy]", say="Four rules. Learn them by heart. They will keep you alive.",
         opt=dict(reveal=0), sfx=[("paper", 0.1)], tense=0.35),
    dict(shot="card", who="walter", tag="[elderly voice] [slowly]", say="One. Nobody in here knows your name. Keep it that way.", opt=dict(reveal=1, hl=0), tense=0.35),
    dict(shot="card", who="walter", tag="[elderly voice] [slowly]", say="Two. The radio drowns out everything that shouldn't be here.", opt=dict(reveal=2, hl=1), tense=0.35),
    dict(shot="card", who="walter", tag="[elderly voice] [slowly]", say="Three. Whatever stands in the light cannot move.", opt=dict(reveal=3, hl=2), tense=0.4),
    dict(shot="card", who="walter", tag="[elderly voice] [slowly]", say="Four. I come back at six. Never earlier.", opt=dict(reveal=4, hl=3), tense=0.4, pad=0.5),
    dict(shot="leave", who="walter", tag="[elderly voice]", say="I'll be back at six. Not a minute earlier.", sfx=[("door", 2.0), ("lock", 3.8)], pad=1.0, tense=0.3),
    dict(shot="corridor_jonas", who="jonas", tag="[nervous]", time="00:12",
         say="Then I was alone. Four hundred thousand square feet of darkness.", sfx=[("footsteps", 0.2)], tense=0.35),
    dict(shot="phone_call", who="jonas", tag="[nervous]", time="00:30", say="At half past twelve, my mom called. And I didn't think.",
         sfx=[("buzz", 0.0), ("buzz", 1.6)], tense=0.4),
    dict(shot="phone_call", who="mama", tag="[warmly]", say="Jonas? Honey? Did you eat something? Jonas, can you hear me?",
         opt=dict(active=True), hall=True, tense=0.4),
    dict(shot="watcher", who="jonas", tag="[whispers]",
         say="Her voice echoed through the entire building. And at the far end of the hallway, something moved.",
         sfx=[("low_hit", 3.6)], tense=0.65, pad=0.7),
    dict(shot="jonas_office", who="jonas", tag="[nervous]", time="01:12", say="Half an hour later. The security room. The radio hissed quietly.",
         radio=0.4, tense=0.4, sfx=[("knock", 4.0)], pad=0.9),
    dict(shot="door3", who="mama_door", tag="[whispers] [trembling voice]", say="Jonas? Honey, it's me. Please open the door. I'm so cold.",
         sfx=[("knock", 0.0)], radio=0.2, tense=0.75, pad=0.5, opt=dict(feet=True)),
    dict(shot="door3", who="jonas", tag="[nervous]", say="That was my mother's voice. Coming from storage room three. Which is locked from the outside.",
         opt=dict(feet=True, push=True), radio=0.2, tense=0.85, sfx=[("knock", 3.0)]),
    dict(shot="door3", who="jonas", tag="[dramatically]", choice=("Go to storage room 3 and open it", "Turn the radio up"),
         say="What should I do? A: Go and open the door. Or B: Turn the radio up.", opt=dict(feet=True), radio=0.2, tense=1.0),
    dict(shot="door3", who="jonas", tag="[softly]", say=END_Q, end=True, pad=1.4, radio=0.2, tense=0.5),
]))

PARTS.append(dict(n=2, name="The Girl on the Escalator", segs=[
    dict(shot="door3", who="mama_door", tag="[whispers]", say="Jonas? Please open the door.", opt=dict(feet=True), title=True,
         sfx=[("knock", 0.2)], tense=0.7, pad=0.5),
    dict(shot="card", who="jonas", tag="[confidently]",
         say="The right answer was B. Rule one: Nobody in here knows my name. Whoever calls it anyway just overheard it.",
         opt=dict(reveal=4, hl=0), tense=0.4),
    dict(shot="card", who="jonas", tag="[confidently]", say="And rule two: The radio drowns out everything that shouldn't be here.",
         opt=dict(reveal=4, hl=1), tense=0.4),
    dict(shot="radio", who="jonas", tag="[nervous]", say="I cranked it up until the speakers crackled. The voice got quieter. And quieter.", radio=1.0, tense=0.6),
    dict(shot="radio", who="mama_door", tag="[whispers] [sad]", say="Why won't you open the door?", radio=1.0, gain=0.5, tense=0.6, pad=0.7),
    dict(shot="phone_msg", who="jonas", tag="[nervous]", time="01:14", say="A minute later, I got a text.", sfx=[("buzz", 0.0)], radio=0.3, tense=0.4, pad=0.6),
    dict(shot="phone_msg", who="jonas", tag="[slowly]", say="My mom had been at home in bed the whole time.", opt=dict(zoom=True), radio=0.3, tense=0.6,
         sfx=[("low_hit", 0.2)], pad=0.6),
    dict(shot="corridor_jonas", who="jonas", tag="[nervous]", time="02:40",
         say="At two forty, I did my rounds. Second floor. That's when I heard someone humming.", sfx=[("footsteps", 0.2), ("hum", 4.0)], tense=0.45),
    dict(shot="escalator", who="jonas", tag="[whispers]", say="On the frozen escalator sat a little girl. Yellow raincoat. Wet rubber boots.",
         sfx=[("hum", 0.0)], tense=0.5),
    dict(shot="mia", who="mia", talk=True, tag="[childlike voice] [sad]", say="I hid when everyone went home. Now I can't find my mommy.", tense=0.5),
    dict(shot="jonas_close", who="jonas", tag="[nervous]", say="She was maybe seven. Her boots were dripping. But it had stopped raining hours ago.",
         sfx=[("drip", 0.5), ("drip", 2.1), ("drip", 3.4)], tense=0.6),
    dict(shot="mia", who="mia", talk=True, tag="[childlike voice] [curious]", say="My name is Mia. What's your name?", opt=dict(tilt=True), tense=0.8, pad=0.5),
    dict(shot="mia", who="jonas", tag="[dramatically]", choice=("“My name is Jonas.”", "“I'm just the security guard.”"),
         say="What do I say? A: My name is Jonas. Or B: I'm just the security guard.", opt=dict(tilt=True), tense=1.0),
    dict(shot="mia", who="jonas", tag="[softly]", say=END_Q, end=True, pad=1.4, opt=dict(tilt=True), tense=0.5),
]))

PARTS.append(dict(n=3, name="What Stands in the Light", segs=[
    dict(shot="mia", who="mia", talk=True, tag="[childlike voice] [curious]", say="What's your name?", opt=dict(tilt=True), title=True, tense=0.7, pad=0.5),
    dict(shot="card", who="jonas", tag="[confidently]", say="The right answer was B. Rule one: Nobody in here knows your name. Keep it that way.",
         opt=dict(reveal=4, hl=0), tense=0.4),
    dict(shot="jonas_close", who="jonas", talk=True, tag="[nervous]", say="I'm just the security guard.", tense=0.6, pad=0.5),
    dict(shot="mia", who="jonas", tag="[whispers]", say="Her smile just stayed there. Frozen.", opt=dict(tilt=True, freeze=True), tense=0.75),
    dict(shot="mia", who="mia_dark", talk=True, tag="[deep voice] [whispers]", say="Too bad.", opt=dict(dark=True), sfx=[("sting", 0.0)], tense=0.95, pad=0.9),
    dict(shot="blackout", who="jonas", tag="[nervous]", say="Then the lights went out. In the entire building.", sfx=[("power_down", 0.0), ("click", 2.6)], tense=0.6, pad=0.6),
    dict(shot="escalator_empty", who="jonas", tag="[whispers]", say="The escalator was empty. Only her stuffed bunny was left.", tense=0.6),
    dict(shot="creature", who="jonas", tag="[whispers] [trembling voice]",
         say="At the end of the hallway, something was standing. It wore her yellow raincoat. But it was almost ten feet tall.",
         opt=dict(dist=1.0), tense=0.8, sfx=[("low_hit", 1.0)]),
    dict(shot="creature", who="jonas", tag="[breathless]", say="My flashlight flickered. And every time it went dark, it was closer.",
         opt=dict(dist=1.0, approach=True), tense=0.95),
    dict(shot="creature", who="jonas", tag="[dramatically]", choice=("Turn around and run", "Keep the light on it and walk backwards"),
         say="What should I do? A: Turn around and run. Or B: Keep the light on it and walk backwards.",
         hint="It's only thirty feet away.", opt=dict(dist=0.45), tense=1.0),
    dict(shot="creature", who="jonas", tag="[softly]", say=END_Q, end=True, pad=1.4, opt=dict(dist=0.45), tense=0.5),
]))

PARTS.append(dict(n=4, name="Knocking on the Glass", segs=[
    dict(shot="creature", who="jonas", tag="[breathless]", say="It came closer. Every time the light went out.", opt=dict(dist=0.45, approach=True), title=True, tense=0.9),
    dict(shot="card", who="jonas", tag="[confidently]", say="The right answer was B. Rule three: Whatever stands in the light cannot move.",
         opt=dict(reveal=4, hl=2), tense=0.4),
    dict(shot="creature_close", who="jonas", tag="[whispers]", say="I kept the beam right on its face. It didn't move. Only its fingers twitched.", tense=0.9),
    dict(shot="creature", who="jonas", tag="[breathless]",
         say="I walked backwards. A hundred and thirty feet. Without blinking. Until I felt the security room door behind me.",
         opt=dict(dist=0.3, recede=True), sfx=[("slam", 6.6)], tense=0.85, pad=0.7),
    dict(shot="jonas_office", who="jonas", tag="[tired]", time="03:20", say="I spent the rest of the night with my back against the wall. The radio at full volume.",
         opt=dict(scared=True), radio=0.9, tense=0.5),
    dict(shot="cctv", who="jonas", tag="[nervous]", time="05:41", say="At five forty-one, someone knocked on the glass door of the main entrance.",
         sfx=[("glass_knock", 1.0), ("glass_knock", 3.4)], radio=0.4, tense=0.6),
    dict(shot="glass_walter", who="walter_door", talk=True, tag="[shouting] [elderly voice]", say="Jonas! Open up! I forgot my keys!",
         sfx=[("glass_knock", 0.0)], tense=0.75),
    dict(shot="glass_walter", who="jonas", tag="[nervous]", say="It was Walter. Soaking wet. He looked terrified.", opt=dict(panic=True), tense=0.75),
    dict(shot="glass_walter", who="walter_door", talk=True, tag="[shouting] [breathless]", say="Please, Jonas! There's something out here! It's getting closer!",
         sfx=[("glass_knock", 0.0), ("glass_knock", 2.2)], opt=dict(shake=True), tense=0.9),
    dict(shot="glass_walter", who="jonas", tag="[dramatically]", choice=("Open the door", "Don't open it"),
         say="What should I do? A: Open the door. Or B: Don't open it. Little hint: there are two clues.",
         hint="Hint: There are TWO clues.", tense=1.0),
    dict(shot="glass_walter", who="jonas", tag="[softly]", say=END_Q, end=True, pad=1.4, tense=0.5),
]))

PARTS.append(dict(n=5, name="Six O'Clock", segs=[
    dict(shot="glass_walter", who="walter_door", talk=True, tag="[shouting] [elderly voice]", say="Jonas! Open up!", title=True,
         sfx=[("glass_knock", 0.0)], tense=0.8, pad=0.5),
    dict(shot="card", who="jonas", tag="[confidently]", say="The right answer was B. Rule four: I come back at six. Never earlier.",
         opt=dict(reveal=4, hl=3), tense=0.4),
    dict(shot="card", who="jonas", tag="[slowly]", say="And Walter didn't even know my name. He never wanted to know it.", opt=dict(reveal=4, hl=0), tense=0.5),
    dict(shot="glass_walter", who="jonas", tag="[whispers]", say="I didn't move. Walter stopped knocking. And smiled. Wider and wider.",
         opt=dict(grin=True), tense=0.85),
    dict(shot="glass_walter", who="creature", talk=True, tag="[deep voice] [slowly]", say="See you tomorrow night, Jonas.",
         opt=dict(grin=True, black=True, close=True), sfx=[("sting", 0.0)], tense=1.0, pad=0.9),
    dict(shot="entrance", who="jonas", tag="[softly]", say="Then he stepped back into the rain. And vanished.", tense=0.5, pad=0.5),
    dict(shot="dawn", who="jonas", tag="[relieved]", time="06:00",
         say="At six sharp, the sun came up. And Walter arrived. The real one. Dry. With two coffees.", sfx=[("keys", 1.0), ("door", 2.5)], tense=0.15),
    dict(shot="walter_dawn", who="walter", talk=True, tag="[elderly voice] [chuckles]", say="Well, kid? You're still alive. Respect.", tense=0.1),
    dict(shot="jonas_close", who="jonas", talk=True, tag="[nervous]", say="You were already here earlier. At five forty-one.", opt=dict(dawn=True), tense=0.3),
    dict(shot="walter_dawn", who="walter", talk=True, tag="[elderly voice] [serious]", say="Did you open the door?", opt=dict(serious=True), tense=0.5, pad=0.4),
    dict(shot="jonas_close", who="jonas", talk=True, tag="[softly]", say="No.", opt=dict(dawn=True), tense=0.5, pad=0.5),
    dict(shot="walter_dawn", who="walter", talk=True, tag="[elderly voice] [serious]", say="Good. The last guy did.", opt=dict(serious=True), tense=0.6, pad=0.7),
    dict(shot="walter_dawn", who="walter", talk=True, tag="[elderly voice] [warmly]", say="Go home and get some sleep. See you tonight... Jonas.", tense=0.6, pad=0.4),
    dict(shot="walter_end", who="jonas", tag="[whispers]", say="He walked down the hallway. And I went ice cold. Because I never told Walter my name.",
         sfx=[("sting", 5.0)], tense=0.9, pad=0.5),
    dict(shot="walter_end", who="jonas", tag="[softly]", say="How many did you get right? Tell me in the comments.", opt=dict(turn=True),
         end=True, final=True, pad=1.6, tense=0.4),
]))


def tts_prompt(part):
    """Whole part as one ElevenLabs prompt; segments separated by pauses."""
    return "\n\n[pause] ".join(f"{s['tag']} {s['say']}" for s in part["segs"])


if __name__ == "__main__":
    tot = 0
    for p in PARTS:
        pr = tts_prompt(p)
        tot += len(pr)
        print(p["n"], len(pr))
    print("total chars", tot)
