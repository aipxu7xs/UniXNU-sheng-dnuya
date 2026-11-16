python3 - <<'PY'
import pathlib
path = pathlib.Path('patches/mesa/turnip-frame-diagnostics.patch')
head = 'diff --git a/src/freedreno/vulkan/tu_frame_diagnostic.h b/src/freedreno/vulkan/tu_frame_diagnostic.h\n--- /dev/null\n'
text = path.read_text()
if text.startswith(head):
    path.write_text(text.replace(head, head.replace('\n--- ', '\nnew file mode 100644\n--- ', 1), 1))
    print('added the new file mode line')
elif 'new file mode 100644' in text.splitlines()[1]:
    print('already has the new file mode line')
else:
    raise SystemExit('unexpected header of ' + str(path))
PY
