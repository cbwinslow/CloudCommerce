import { useState } from 'react';
import { useUser } from '@clerk/nextjs';

interface FormData {
  images: File[];
  summary: string;
  category?: string;
  condition?: string;
  // Advanced fields
}

export default function SubmissionForm() {
  const { user } = useUser();
  const [formData, setFormData] = useState<FormData>({ images: [], summary: '' });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const form = new FormData();
    formData.images.forEach((img) => form.append('images', img));
    form.append('summary', formData.summary);
    if (formData.category) form.append('category', formData.category);
    if (formData.condition) form.append('condition', formData.condition);

    const res = await fetch('/api/submit', {
      method: 'POST',
      body: form,
    });
    const data = await res.json();
    setResult(data);
    setLoading(false);
  };

  if (!user) return null;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Simple Mode */}
      <div>
        <label>Images (drag/drop or select):</label>
        <input
          type="file"
          multiple
          accept="image/*"
          onChange={(e) => setFormData({ ...formData, images: Array.from(e.target.files || []) })}
          className="block w-full"
        />
      </div>
      <div>
        <label>Text Summary:</label>
        <textarea
          value={formData.summary}
          onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
          className="w-full p-2 border"
          placeholder="Describe the item..."
        />
      </div>
      {/* Advanced Mode - Toggle */}
      <div className="space-y-2">
        <label>Category (optional):</label>
        <select
          onChange={(e) => setFormData({ ...formData, category: e.target.value })}
          className="w-full p-2 border"
        >
          <option value="">Select...</option>
          <option value="electronics">Electronics</option>
          <option value="clothing">Clothing</option>
          {/* Add more */}
        </select>
        <label>Condition (optional):</label>
        <select
          onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
          className="w-full p-2 border"
        >
          <option value="">Select...</option>
          <option value="new">New</option>
          <option value="used">Used</option>
          <option value="damaged">Damaged</option>
        </select>
      </div>
      <button type="submit" disabled={loading} className="bg-blue-500 text-white px-4 py-2 rounded">
        {loading ? 'Processing...' : 'Submit for Analysis'}
      </button>
      {result && (
        <div className="mt-8 p-4 bg-green-100">
          <h2>Listings Generated:</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
          {/* CSV Download Button */}
          <a href={`data:text/csv;charset=utf-8,${encodeURIComponent(result.csv)}`} download="listings.csv">
            Download CSV
          </a>
        </div>
      )}
    </form>
  );
}