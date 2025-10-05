import { useState, useCallback, useRef } from 'react';
import { useUser } from '@clerk/nextjs';

interface FormData {
  images: File[];
  summary: string;
  category?: string;
  condition?: string;
}

export default function SubmissionForm() {
  const { user } = useUser();
  const [formData, setFormData] = useState<FormData>({ images: [], summary: '' });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [dragActive, setDragActive] = useState(false);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  // Handle drop event
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  }, []);

  // Handle file selection
  const handleFiles = useCallback((files: File[]) => {
    const imageFiles = files.filter(file => file.type.startsWith('image/'));

    if (imageFiles.length === 0) {
      setErrors({ images: 'Please select only image files' });
      return;
    }

    if (imageFiles.length > 10) {
      setErrors({ images: 'Maximum 10 images allowed' });
      return;
    }

    setFormData(prev => ({ ...prev, images: imageFiles }));
    setErrors({});

    // Create previews
    const previews = imageFiles.map(file => URL.createObjectURL(file));
    setImagePreviews(previews);
  }, []);

  // Handle file input change
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
  };

  // Remove image
  const removeImage = (index: number) => {
    const newImages = formData.images.filter((_, i) => i !== index);
    const newPreviews = imagePreviews.filter((_, i) => i !== index);

    // Revoke old preview URLs
    imagePreviews.forEach((preview, i) => {
      if (i === index) URL.revokeObjectURL(preview);
    });

    setFormData(prev => ({ ...prev, images: newImages }));
    setImagePreviews(newPreviews);
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const newErrors: {[key: string]: string} = {};
    if (formData.images.length === 0) newErrors.images = 'Please upload at least one image';
    if (!formData.summary.trim()) newErrors.summary = 'Please provide a description';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      const form = new FormData();
      formData.images.forEach((img) => form.append('images', img));
      form.append('summary', formData.summary);
      if (formData.category) form.append('category', formData.category);
      if (formData.condition) form.append('condition', formData.condition);

      const res = await fetch('/api/submit', {
        method: 'POST',
        body: form,
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error('Submission error:', error);
      setErrors({ submit: 'Failed to process your request. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Submit Item for Analysis</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Image Upload Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Item Images *
          </label>

          {/* Drag and Drop Zone */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
              dragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*"
              onChange={handleFileInputChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />

            <div className="space-y-2">
              <div className="text-gray-600">
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div className="text-sm text-gray-600">
                <span className="font-medium text-blue-600 hover:text-blue-500">Upload files</span> or drag and drop
              </div>
              <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB each (max 10 images)</p>
            </div>
          </div>

          {errors.images && (
            <p className="mt-1 text-sm text-red-600">{errors.images}</p>
          )}

          {/* Image Previews */}
          {imagePreviews.length > 0 && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
              {imagePreviews.map((preview, index) => (
                <div key={index} className="relative group">
                  <img
                    src={preview}
                    alt={`Preview ${index + 1}`}
                    className="w-full h-24 object-cover rounded-lg border"
                  />
                  <button
                    type="button"
                    onClick={() => removeImage(index)}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Description Section */}
        <div>
          <label htmlFor="summary" className="block text-sm font-medium text-gray-700 mb-2">
            Item Description *
          </label>
          <textarea
            id="summary"
            rows={4}
            value={formData.summary}
            onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            placeholder="Describe your item in detail... Include brand, model, condition, features, dimensions, etc."
          />
          {errors.summary && (
            <p className="mt-1 text-sm text-red-600">{errors.summary}</p>
          )}
        </div>

        {/* Category and Condition */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
              Category (Optional)
            </label>
            <select
              id="category"
              value={formData.category || ''}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="">Select category...</option>
              <option value="electronics">Electronics</option>
              <option value="clothing">Clothing & Accessories</option>
              <option value="home-garden">Home & Garden</option>
              <option value="sports">Sports & Recreation</option>
              <option value="collectibles">Collectibles</option>
              <option value="books">Books & Media</option>
              <option value="automotive">Automotive</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label htmlFor="condition" className="block text-sm font-medium text-gray-700 mb-2">
              Condition (Optional)
            </label>
            <select
              id="condition"
              value={formData.condition || ''}
              onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="">Select condition...</option>
              <option value="new">New</option>
              <option value="like-new">Like New</option>
              <option value="good">Good</option>
              <option value="fair">Fair</option>
              <option value="poor">Poor</option>
            </select>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-between">
          <button
            type="submit"
            disabled={loading || formData.images.length === 0}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            {loading ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing Images...
              </div>
            ) : (
              'Generate Listings'
            )}
          </button>

          {formData.images.length > 0 && (
            <span className="text-sm text-gray-500">
              {formData.images.length} image{formData.images.length !== 1 ? 's' : ''} selected
            </span>
          )}
        </div>

        {errors.submit && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{errors.submit}</p>
          </div>
        )}
      </form>

      {/* Results Section */}
      {result && (
        <div className="mt-8 p-6 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="text-lg font-semibold text-green-900 mb-4">✅ Analysis Complete!</h3>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Generated Listings</h4>
              <pre className="text-xs bg-white p-3 rounded border overflow-auto max-h-48">
                {JSON.stringify(result.listings, null, 2)}
              </pre>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Actions</h4>
              <div className="space-y-2">
                <button
                  onClick={() => {
                    const blob = new Blob([result.csv], { type: 'text/csv' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'listings.csv';
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                  className="block w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-medium"
                >
                  📥 Download CSV
                </button>

                <button
                  onClick={() => {
                    navigator.clipboard.writeText(result.csv);
                    alert('CSV copied to clipboard!');
                  }}
                  className="block w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded text-sm font-medium"
                >
                  📋 Copy CSV
                </button>
              </div>

              {result.recommendedPrice && (
                <div className="mt-4 p-3 bg-blue-50 rounded">
                  <p className="text-sm text-blue-900">
                    <strong>Recommended Price:</strong> ${result.recommendedPrice}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
