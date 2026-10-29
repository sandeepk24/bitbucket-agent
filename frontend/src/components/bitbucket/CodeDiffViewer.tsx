import { DiffEditor } from "@monaco-editor/react";
import "@/lib/monaco";
import { languageFromPath } from "@/lib/comparison";

interface CodeDiffViewerProps {
  path: string;
  original: string;
  modified: string;
  sideBySide: boolean;
}

export function CodeDiffViewer({ path, original, modified, sideBySide }: CodeDiffViewerProps) {
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
    />
  );
}
