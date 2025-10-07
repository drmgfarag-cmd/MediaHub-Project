import sys, re, json, pathlib
p = pathlib.Path(__file__).resolve().parents[1] / 'web' / 'assets' / 'ui_enhance.js'
s = p.read_text(encoding='utf-8', errors='ignore')
def bal(s, a, b):
    v=0
    for ch in s:
        if ch==a: v+=1
        elif ch==b: v-=1
    return v
rep = {
  "balanced_curly": bal(s,'{','}') == 0,
  "balanced_round": bal(s,'(',')') == 0,
  "balanced_square": bal(s,'[',']') == 0,
  "strings_even_single": (s.count("'") - s.count("\\'")) % 2 == 0,
  "strings_even_double": (s.count('"') - s.count('\\"')) % 2 == 0,
  "strings_even_backticks": (s.count('`') - s.count('\\`')) % 2 == 0,
}
print(json.dumps(rep, indent=2))
