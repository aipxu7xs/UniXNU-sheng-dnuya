python3 - <<'PY'
import ast, pathlib
p = pathlib.Path('UniXNU/kits/XnuPrelink/fileset_layout.py')
t = p.read_text()
anchor = '        self.validate()'
assert t.count(anchor) == 1, 'layout validation anchor must be unique'
lines = ["        print('LAYOUT SEGMENTS', self.describe(), flush=True)","        print('LAYOUT ROOTS', {n: (hex(s['va']), hex(s['size'])) for n, s in self.roots.items()}, flush=True)","        diagnostic_placed = []","        for segment in self.native.segments:","            if not segment['size']:","                continue","            begin = self.placements[segment['name']]","            end = self.end(segment['name'])","            for b, e in self.occupied:","                if begin < e and b < end:","                    print('LAYOUT OVERLAP retained', segment['name'], hex(begin), hex(end), hex(b), hex(e), 'bytes', hex(min(end, e) - max(begin, b)), flush=True)","            print('LAYOUT USED', segment['name'], hex(self.used(segment['name'])), 'span', hex(self.span(segment['name'])), flush=True)","            for n, b, e in diagnostic_placed:","                if begin < e and b < end:","                    print('LAYOUT OVERLAP native', segment['name'], n, hex(begin), hex(end), hex(b), hex(e), flush=True)","            diagnostic_placed.append((segment['name'], begin, end))","        print('LAYOUT DATA SECTIONS', [s for s in self.native.sections if s.get('segment') == '__DATA'], flush=True)","        self.validate()"]
replacement = chr(10).join(lines)
t = t.replace(anchor, replacement, 1)
assert replacement in t
ast.parse(t)
p.write_text(t)
PY
