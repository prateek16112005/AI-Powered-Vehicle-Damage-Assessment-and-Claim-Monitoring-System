"use client";

import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      alert("Please select an image first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: "Upload failed. Check backend connection." });
    }

    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-white text-black p-8">
      <h1 className="text-3xl font-bold mb-6">AI Vehicle Damage Assessment</h1>

      <input
        type="file"
        accept="image/*"
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
          }
        }}
        className="mb-4"
      />

      <div className="mt-4">
        <button
          onClick={handleUpload}
          className="bg-red-600 text-white px-5 py-2 rounded"
        >
          {loading ? "Analyzing..." : "Upload and Analyze"}
        </button>
      </div>

      {result && (
        <div className="mt-8 border rounded p-4 shadow">
          <h2 className="text-xl font-semibold mb-3">Result</h2>
          <pre className="whitespace-pre-wrap text-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </main>
  );
}