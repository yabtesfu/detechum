"""Writing tasks for the AI written student essays of eval_plan_v2.

Every generator, local or remote, gets its tasks from `tasks()`, so the essays of different models share
topics, kinds of essay, lengths and voices. The topics are the 44 prompt names of ELLIPSE, so that AI and
human essays on one topic can be kept in the same split. ELLIPSE publishes the names only, so the task
text below is ours.

Each task records everything plan §1 asks for: the instruction given to the model, the topic, the kind of
essay, the target length and the voice. The generator, its date and its decoding settings are added by the
script that runs it.
"""

import random

TOPICS = [
    "Distance learning", "Career commitment", "Success and failure", "Being busy", "Positive attitudes",
    "Impact of technology", "Trying something beyond what you have mastered", "First impressions",
    "Three-year high school program", "Individuality", "Four-day work week", "Working with a group or alone",
    "Self-reliance", "Lunch menus", "Influences of character", "Extended school day", "Year-round school",
    "Influencing behavior", "Cell phones in classrooms", "Internships and shadowing",
    "Enjoyable educational activities", "Praising student work", "Afterschool homework club", "Imagination",
    "Curfews for teenagers", "Spending time outdoors", "Controlling extracurricular involvement",
    "Seeking multiple opinions", "Creative arts requirement", "Community service", "Places to visit",
    "Letter to employer", "Cell phones at school", "Talents and skills", "Mandatory extracurricular activities",
    "Lessons with elementary school students", "Grades for extracurricular activities", "Future accomplishments",
    "Benefits of a problem", "Benefits of a good attitude", "Learning from the experience of others", "Honesty",
    "Setting our aim", "Summer projects",
]

KINDS = {
    "argument": "Write an essay for a school assignment on the topic \"{topic}\". Take a position and support "
                "it with reasons and examples.",
    "personal": "Write a personal essay for a school assignment on the topic \"{topic}\". Tell a story from "
                "your own life that relates to the topic.",
    "explanatory": "Write an essay for a school assignment that explains the topic \"{topic}\" to a reader "
                   "who knows little about it.",
}

LENGTHS = [180, 300, 450, 650]  # target words; they spread the essays over the length bands of plan §1

VOICES = {
    "plain": "",
    "grade": " Write it the way a student in grade {grade} would write it.",
    "learner": " Write it the way a high school student who is still learning English would write it.",
}

FORMAT = " Write about {words} words. Give plain text only: no title, no headings and no lists."


def tasks(n: int, seed: int, id_prefix: str, lengths: list[int] = LENGTHS) -> list[dict]:
    """`n` tasks drawn with a fixed seed. Topics, kinds and target lengths are balanced by cycling; voices
    and grades are drawn at random."""
    rng = random.Random(seed)
    topics = TOPICS * (n // len(TOPICS) + 1)
    rng.shuffle(topics)
    out = []
    for i in range(n):
        kind = list(KINDS)[i % len(KINDS)]
        words = lengths[(i // len(KINDS)) % len(lengths)]
        voice = list(VOICES)[rng.randrange(len(VOICES))]
        grade = rng.randint(8, 12)
        instruction = (KINDS[kind] + VOICES[voice] + FORMAT).format(topic=topics[i], grade=grade, words=words)
        out.append({"id": f"{id_prefix}{i:04d}", "topic": topics[i], "kind": kind, "target_words": words,
                    "voice": voice, "grade": grade if voice == "grade" else None, "instruction": instruction})
    return out
