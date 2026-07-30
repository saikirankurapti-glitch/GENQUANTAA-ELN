import glob
import re

for file in glob.glob('migrations/versions/*.py'):
    with open(file, 'r') as f:
        text = f.read()
    
    def replacer(match):
        args_str = match.group(1)
        # Convert all uppercase strings like 'ACTIVE' to 'active'
        args_str = re.sub(r"'([A-Z_]+)'", lambda m: f"'{m.group(1).lower()}'", args_str)
        return f"sa.Enum({args_str})"
        
    new_text = re.sub(r"sa\.Enum\((.*?)\)", replacer, text)
    with open(file, 'w') as f:
        f.write(new_text)

print("Fixed Enums in migrations.")
