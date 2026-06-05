import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('frontend/src/App.tsx', encoding='utf-8') as f:
    content = f.read()

# Mapping emoji -> PrimeIcon component or clean text
# We'll replace inline emoji with <i className="pi pi-X"/> or just remove them from labels
replacements_text = [
    # Close button
    ('\u2715', '<i className="pi pi-times" />'),
    # Graduation cap - remove from div 
    ('\U0001f393', ''),
    # In nav labels - remove emoji prefix from strings
    ('\U0001f4ca Trang ch\u1ee7', 'Trang ch\u1ee7'),
    ('\U0001f4da Ch\u01b0\u01a1ng tr\u00ecnh khung', 'Ch\u01b0\u01a1ng tr\u00ecnh khung'),
    ('\U0001f916 D\u1ef1 b\u00e1o \u0111i\u1ec3m', 'D\u1ef1 b\u00e1o \u0111i\u1ec3m'),
    ('\U0001f9ee C\u00f4ng c\u1ee5 t\u00ednh \u0111i\u1ec3m', 'C\u00f4ng c\u1ee5 t\u00ednh \u0111i\u1ec3m'),
    ('\U0001f4dd C\u00e1c m\u00f4n g\u1ea7n nh\u1ea5t', 'C\u00e1c m\u00f4n g\u1ea7n nh\u1ea5t'),
    ('\U0001f4da Ch\u01b0\u01a1ng tr\u00ecnh khung - Kh\u00f3a h\u1ecdc KHDL 2023', 'Ch\u01b0\u01a1ng tr\u00ecnh khung - Kh\u00f3a h\u1ecdc KHDL 2023'),
    ('\u2713 \u0110\u1ea1t', '\u0110\u1ea1t'),
    ('\u2713', '\u0110\u1ea1t'),
    ('\U0001f916 D\u1ef1 b\u00e1o \u0110i\u1ec3m thi cu\u1ed1i k\u1ef3', 'D\u1ef1 b\u00e1o \u0110i\u1ec3m thi cu\u1ed1i k\u1ef3'),
    ('\U0001f9ee C\u00f4ng c\u1ee5 T\u00ednh \u0111i\u1ec3m H\u1ecdc v\u1ee5 IUH', 'C\u00f4ng c\u1ee5 T\u00ednh \u0111i\u1ec3m H\u1ecdc v\u1ee5 IUH'),
    ('Qu\u1ea3n l\u00fd m\u00f4n ph\u1ee5 tr\u00e1ch', 'Qu\u1ea3n l\u00fd m\u00f4n ph\u1ee5 tr\u00e1ch'),
    ('Nh\u1eadp v\u00e0 s\u1eeda \u0111i\u1ec3m SV', 'Nh\u1eadp v\u00e0 s\u1eeda \u0111i\u1ec3m SV'),
    ('N\u1ea1p t\u1ec7p \u0111i\u1ec3m CSV/XLSX', 'N\u1ea1p t\u1ec7p \u0111i\u1ec3m CSV/XLSX'),
]

# Also replace any remaining isolated emoji chars
import re
# Unicode emoji ranges
emoji_re = re.compile(r'[\U0001F300-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\u2600-\u27BF\u2B50\u2B55]+')

for old, new in replacements_text:
    content = content.replace(old, new)

# Clean up remaining stray emojis in string literals (inside quotes)
def replace_emoji_in_string(m):
    s = m.group(0)
    return emoji_re.sub('', s)

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

# Count remaining
remaining = emoji_re.findall(content)
print(f'Done. Remaining emoji instances: {len(remaining)}')
if remaining:
    print('Sample remaining:', remaining[:10])
