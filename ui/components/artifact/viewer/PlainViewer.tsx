"use client";

export default function PlainViewer({ data }: { data: string }) {
  return <div className="overflow-auto">
    <pre className="m-0 p-2 text-break">{data}</pre>
  </div>
}