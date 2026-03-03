'use client';

import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import DOMPurify from 'dompurify';
import rehypeSanitize from 'rehype-sanitize';

type MarkdownSegment =
    | { type: 'markdown'; content: string }
    | { type: 'table'; header: string[]; rows: string[][] };

const SAFE_COMPONENTS: Components = {
    script: () => null,
    style: () => null,
    a: ({ href, children, ...props }) => {
        const safeHref = href && /^(https?:|mailto:|tel:|\/|#)/i.test(href) ? href : '#';
        return (
            <a href={safeHref} target="_blank" rel="noopener noreferrer" {...props}>
                {children}
            </a>
        );
    },
};

function isTableSeparator(line: string): boolean {
    return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line.trim());
}

function splitTableRow(line: string): string[] {
    return line
        .trim()
        .replace(/^\|/, '')
        .replace(/\|$/, '')
        .split('|')
        .map((c) => c.trim());
}

function parseMarkdownSegments(content: string): MarkdownSegment[] {
    const lines = content.split('\n');
    const segments: MarkdownSegment[] = [];
    let markdownBuffer: string[] = [];
    let i = 0;

    const flushMarkdown = () => {
        if (!markdownBuffer.length) return;
        const block = markdownBuffer.join('\n').trim();
        if (block) segments.push({ type: 'markdown', content: block });
        markdownBuffer = [];
    };

    while (i < lines.length) {
        const current = lines[i];
        const next = lines[i + 1];

        const looksLikeTableHeader = current.includes('|') && next && isTableSeparator(next);
        if (!looksLikeTableHeader) {
            markdownBuffer.push(current);
            i += 1;
            continue;
        }

        flushMarkdown();
        const header = splitTableRow(current);
        const rows: string[][] = [];
        i += 2; // skip header + separator

        while (i < lines.length && lines[i].includes('|') && lines[i].trim() !== '') {
            rows.push(splitTableRow(lines[i]));
            i += 1;
        }

        if (header.length > 0 && rows.length > 0) {
            segments.push({ type: 'table', header, rows });
        } else {
            markdownBuffer.push(current);
        }
    }

    flushMarkdown();
    return segments.length ? segments : [{ type: 'markdown', content }];
}

function coerceStructuredAssistantText(content: string): string {
    const trimmed = content.trim();
    if (!trimmed) return content;
    const looksLikeJson = (trimmed.startsWith('{') && trimmed.endsWith('}'))
        || (trimmed.startsWith('[') && trimmed.endsWith(']'));
    if (!looksLikeJson) return content;

    try {
        const parsed = JSON.parse(trimmed) as Record<string, unknown> | unknown[];
        if (Array.isArray(parsed)) return content;
        const candidateKeys = ['assistant_message', 'response', 'message', 'summary', 'content'];
        for (const key of candidateKeys) {
            const value = parsed[key];
            if (typeof value === 'string' && value.trim()) return value;
        }
        return 'I prepared your structured travel output and rendered it in the itinerary panel.';
    } catch {
        return content;
    }
}

interface MarkdownRendererProps {
    content: string;
    coerceStructuredContent?: boolean;
}

export function MarkdownRenderer({
    content,
    coerceStructuredContent = false,
}: MarkdownRendererProps) {
    const normalized = coerceStructuredContent ? coerceStructuredAssistantText(content) : content;
    const safeContent = typeof window !== 'undefined'
        ? DOMPurify.sanitize(normalized, {
            USE_PROFILES: { html: true },
            ALLOW_DATA_ATTR: false,
            ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto|tel):|\/|#)/i,
            FORBID_TAGS: ['script', 'style', 'iframe', 'form', 'input', 'button'],
            FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'data-*'],
        })
        : normalized;

    const segments = parseMarkdownSegments(safeContent);

    return (
        <div className="space-y-3">
            {segments.map((segment, idx) => {
                if (segment.type === 'markdown') {
                    return (
                        <ReactMarkdown key={`md-${idx}`} rehypePlugins={[rehypeSanitize]} components={SAFE_COMPONENTS}>
                            {segment.content}
                        </ReactMarkdown>
                    );
                }

                return (
                    <div key={`tbl-${idx}`} className="overflow-x-auto rounded-xl border border-black/10 dark:border-white/10">
                        <table className="min-w-full text-sm">
                            <thead className="bg-black/5 dark:bg-white/5">
                                <tr>
                                    {segment.header.map((cell, hIdx) => (
                                        <th
                                            key={`h-${hIdx}`}
                                            className="px-3 py-2 text-left font-semibold whitespace-nowrap"
                                            style={{ color: 'var(--text-primary)' }}
                                        >
                                            {cell}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {segment.rows.map((row, rIdx) => (
                                    <tr key={`r-${rIdx}`} className="border-t border-black/5 dark:border-white/5">
                                        {segment.header.map((_, cIdx) => (
                                            <td key={`c-${rIdx}-${cIdx}`} className="px-3 py-2 align-top">
                                                {row[cIdx] || ''}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                );
            })}
        </div>
    );
}
