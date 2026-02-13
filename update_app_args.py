import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Add --key argument
arg_pattern = r'(parser\.add_argument\("--vocal-strength", type=float, default=1.2, help="Strength of vocal steering \(default: 1.2\)"\))'
arg_replacement = r'\1\n    parser.add_argument("--key", type=str, help="Musical key (e.g. \'C Minor\')")'
content = re.sub(arg_pattern, arg_replacement, content)

# 2. Update run method signature
run_pattern = r'(def run\(self, genre, user_direction, seed=None, artist_style=None, artist_background=None, song_title=None, album_name=None, track_number=None, vocals="auto", vocal_strength=1.2)\):'
run_replacement = r'\1, key=None):'
content = re.sub(run_pattern, run_replacement, content)

# 3. Update initial_state in run method
state_pattern = r'("vocal_strength": vocal_strength)'
state_replacement = r'\1,\n            "key": key'
content = re.sub(state_pattern, state_replacement, content)

# 4. Update flow.run call in Album mode
# Note: The album loop calls flow.run with many args.
# We need to find the call inside the album loop.
# It looks like:
#             final_state = flow.run(
#                 args.genre,
#                 current_direction,
#                 seed=master_seed,
#                 artist_style=persistent_artist_style,
#                 artist_background=persistent_artist_background,
#                 song_title=song_title,
#                 album_name=album_name,
#                 track_number=i,
#                 vocals=args.vocals,
#                 vocal_strength=args.vocal_strength
#             )
album_run_pattern = r'(vocal_strength=args\.vocal_strength)(\n\s+\))'
album_run_replacement = r'\1,\n                key=args.key\2'
# This needs to be applied carefully. There are two flow.run calls.
# One in album mode (indented), one in single mode.
# The single mode one:
# final_state = flow.run(args.genre, args.direction, vocals=args.vocals, vocal_strength=args.vocal_strength)

# Let's handle them separately or globally if the pattern matches both correctly.
# The album one has newlines. The single one is on one line or wraps differently.

# Regex for the album call (multiline)
content = re.sub(r'(vocal_strength=args\.vocal_strength)(\n\s+\))', r'\1,\n                key=args.key\2', content)

# Regex for the single song call
# It might be: flow.run(args.genre, args.direction, vocals=args.vocals, vocal_strength=args.vocal_strength)
single_run_pattern = r'(flow\.run\(args\.genre, args\.direction, vocals=args\.vocals, vocal_strength=args\.vocal_strength)(\))'
single_run_replacement = r'\1, key=args.key\2'
content = re.sub(single_run_pattern, single_run_replacement, content)

with open("app.py", "w") as f:
    f.write(content)
