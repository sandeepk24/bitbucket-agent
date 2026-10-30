import { DiffEditor } from "@monaco-editor/react";
import "@/lib/monaco";
import { languageFromPath } from "@/lib/comparison";

interface CodeDiffViewerProps {
  path: string;
  original: string;
  modified: string;
  sideBySide: boolean;
  highlightBeforeLines?: number[];
  highlightAfterLines?: number[];
}

export function CodeDiffViewer({
  path,
  original,
  modified,
  sideBySide,
  highlightBeforeLines = [],
  highlightAfterLines = [],
}: CodeDiffViewerProps) {
  return (
    <DiffEditor
      height="100%"
      theme="vs-dark"
      language={languageFromPath(path)}
      original={original}
      modified={modified}
      options={{
        readOnly: true,
        originalEditable: false,
        renderSideBySide: sideBySide,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        renderIndicators: true,
        ignoreTrimWhitespace: false,
      }}
      onMount={(editor, monaco) => {
        const originalEditor = editor.getOriginalEditor();
        const modifiedEditor = editor.getModifiedEditor();
        const lineHits = (lines: number[]) =>
          lines.map((line) => ({
            range: new monaco.Range(line, 1, line, 1),
            options: {
              isWholeLine: true,
              className: "analysis-line-hit",
              linesDecorationsClassName: "analysis-line-gutter",
            },
          }));
        originalEditor.deltaDecorations([], lineHits(highlightBeforeLines));
        modifiedEditor.deltaDecorations([], lineHits(highlightAfterLines));
        if (highlightAfterLines[0]) {
          modifiedEditor.revealLineInCenter(highlightAfterLines[0]);
        } else if (highlightBeforeLines[0]) {
          originalEditor.revealLineInCenter(highlightBeforeLines[0]);
        }
      }}
    />
  );
}
