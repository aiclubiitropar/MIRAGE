import React, { useState, useEffect } from 'react';
import Cookies from 'js-cookie';

// --- Helper Components ---

const SunIcon = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
  </svg>
);

const MoonIcon = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
  </svg>
);

const MirageLogo = ({ className }) => (
    <svg className={className} viewBox="0 0 200 50" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="mirageGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style={{stopColor: 'rgb(99, 102, 241)', stopOpacity: 1}} />
                <stop offset="100%" style={{stopColor: 'rgb(219, 39, 119)', stopOpacity: 1}} />
            </linearGradient>
        </defs>
        <text x="10" y="40" fontFamily="Arial, sans-serif" fontSize="40" fontWeight="bold" fill="url(#mirageGradient)">MIRAGE</text>
    </svg>
);

const IotaClusterLogo = ({ className }) => (
    <svg className={className} viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <path fill="currentColor" d="M50 0 L61.8 38.2 L100 38.2 L69.1 61.8 L80.9 100 L50 76.4 L19.1 100 L30.9 61.8 L0 38.2 L38.2 38.2 Z" />
    </svg>
);

// Helper to convert file to base64
const toBase64 = file => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = error => reject(error);
});

// --- Main App Component ---

export default function App() {
  const [theme, setTheme] = useState('dark');
  const [originalImage, setOriginalImage] = useState(null);
  const [originalFile, setOriginalFile] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [editedImage, setEditedImage] = useState(null);
  const [gallery, setGallery] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(theme);
  }, [theme]);

  useEffect(() => {
    const lastImage = Cookies.get('lastGeneratedImage');
    if (lastImage) {
      setEditedImage(lastImage);
    }
  }, []);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
  };

  const handleImageChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      setEditedImage(null);
      setError("");
      setOriginalFile(file);
      setOriginalImage(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!originalFile || !prompt) {
      setError("Please upload an image and provide an editing prompt.");
      return;
    }
    setLoading(true);
    setError("");
    setEditedImage(null);

    try {
      const formData = new FormData();
      formData.append("image", originalFile);
      formData.append("prompt", prompt);

      console.log("Sending request with:", {
        image: originalFile.name,
        prompt: prompt,
        fileSize: originalFile.size,
        fileType: originalFile.type
      });

      const response = await fetch("http://localhost:5000/edit-image/", {
        method: "POST",
        body: formData,
      });

      console.log("Response status:", response.status);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `API error: ${response.status}`);
      }

      const blob = await response.blob();
      const imageUrl = URL.createObjectURL(blob);
      setEditedImage(imageUrl);
      setGallery(prevGallery => [imageUrl, ...prevGallery]);

      // Save the last generated image in cookies
      Cookies.set('lastGeneratedImage', imageUrl, { expires: 7 });

    } catch (err) {
      console.error("Error in handleSubmit:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.add('dragging');
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('dragging');
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('dragging');

    const file = e.dataTransfer.files[0];
    if (file) {
      setEditedImage(null);
      setError("");
      setOriginalFile(file);
      setOriginalImage(URL.createObjectURL(file));
    }
  };

  // --- Embedded Styles ---
  // All styling is defined here to make the component self-contained.
  const styles = `
    :root {
      --bg-light: #f3f4f6; --text-light: #1f2937; --card-light: #ffffff; --border-light: #e5e7eb;
      --bg-dark: #111827; --text-dark: #f9fafb; --card-dark: #1f2937; --border-dark: #374151;
      --indigo-600: #4f46e5; --indigo-700: #4338ca; --indigo-400: #818cf8; --indigo-800: #3730a3;
      --gray-400: #9ca3af; --gray-500: #6b7280;
    }
    .dark { --bg-main: var(--bg-dark); --text-main: var(--text-dark); --bg-card: var(--card-dark); --border-main: var(--border-dark); }
    .light { --bg-main: var(--bg-light); --text-main: var(--text-light); --bg-card: var(--card-light); --border-main: var(--border-light); }
    
    body { font-family: sans-serif; }
    .app-container { background-color: var(--bg-main); color: var(--text-main); min-height: 100vh; transition: background-color 0.3s, color 0.3s; }
    .container { width: 100%; margin-left: auto; margin-right: auto; padding: 1rem; }
    @media (min-width: 640px) { .container { max-width: 640px; padding: 1.5rem; } }
    @media (min-width: 768px) { .container { max-width: 768px; padding: 2rem; } }
    @media (min-width: 1024px) { .container { max-width: 1024px; } }
    @media (min-width: 1280px) { .container { max-width: 1280px; } }

    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
    @media (min-width: 768px) { .header { margin-bottom: 2rem; } }
    .logo-container { display: flex; align-items: center; gap: 0.75rem; }
    .logo { height: 2rem; width: auto; }
    @media (min-width: 768px) { .logo { height: 2.5rem; } }
    .logo-subtitle { font-size: 0.875rem; font-weight: 300; color: var(--gray-500); }
    .dark .logo-subtitle { color: var(--gray-400); }
    @media (max-width: 639px) { .hidden-sm { display: none; } }
    
    .theme-toggle { padding: 0.5rem; border-radius: 9999px; color: var(--gray-500); }
    .dark .theme-toggle { color: var(--gray-400); }
    .theme-toggle:hover { background-color: #e5e7eb; }
    .dark .theme-toggle:hover { background-color: #374151; }
    .theme-toggle:focus { outline: 2px solid transparent; outline-offset: 2px; box-shadow: 0 0 0 2px var(--indigo-600); }
    .icon-size { width: 1.5rem; height: 1.5rem; }
    
    .main-grid { display: grid; grid-template-columns: repeat(1, minmax(0, 1fr)); gap: 1.5rem; }
    @media (min-width: 768px) { .main-grid { gap: 2rem; } }
    @media (min-width: 1024px) { .main-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); } }
    
    .control-panel { background-color: var(--bg-card); border-radius: 1rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); padding: 1.5rem; height: fit-content; }
    @media (min-width: 1024px) { .lg-col-span-2 { grid-column: span 2 / span 2; } }
    .panel-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.25rem; }
    @media (min-width: 640px) { .panel-title { font-size: 1.5rem; } }
    .panel-subtitle { color: var(--gray-500); margin-bottom: 1.5rem; }
    .dark .panel-subtitle { color: var(--gray-400); }
    
    .form { display: flex; flex-direction: column; gap: 1.5rem; }
    .form-label { display: block; font-size: 0.875rem; font-weight: 500; color: #374151; margin-bottom: 0.5rem; }
    .dark .form-label { color: #d1d5db; }
    
    .upload-area { margin-top: 0.25rem; display: flex; justify-content: center; padding: 1.25rem 1.5rem; border: 2px dashed var(--border-main); border-radius: 0.375rem; text-align: center; cursor: pointer; transition: all 0.3s ease; }
    .upload-area:hover { border-color: var(--indigo-600); background-color: rgba(79, 70, 229, 0.05); }
    .upload-area.has-image { padding: 0; border: 2px solid var(--border-main); aspect-ratio: 16 / 9; min-height: 200px; position: relative; }
    .upload-area.has-image:hover { border-color: var(--indigo-600); }
    
    .uploaded-image-preview { width: 100%; height: 100%; position: relative; border-radius: 0.375rem; overflow: hidden; }
    .preview-image { width: 100%; height: 100%; object-fit: cover; }
    .upload-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0, 0, 0, 0.6); display: flex; flex-direction: column; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s ease; }
    .upload-area.has-image:hover .upload-overlay { opacity: 1; }
    .upload-icon-small { width: 2rem; height: 2rem; color: white; margin-bottom: 0.5rem; }
    .upload-overlay-text { color: white; font-size: 0.875rem; font-weight: 500; }
    
    .upload-icon { margin: 0 auto; height: 3rem; width: 3rem; color: var(--gray-400); }
    .upload-text { font-size: 0.875rem; color: var(--gray-500); }
    .dark .upload-text { color: var(--gray-400); }
    .upload-browse { cursor: pointer; border-radius: 0.375rem; font-weight: 500; color: var(--indigo-600); }
    .dark .upload-browse { color: #818cf8; }
    .upload-browse:hover { color: #4338ca; }
    .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border-width: 0; }
    .upload-hint { font-size: 0.75rem; color: var(--gray-500); }
    
    .prompt-input { width: 100%; padding: 0.75rem; background-color: #f9fafb; border: 1px solid #d1d5db; border-radius: 0.5rem; transition: border-color 0.2s, box-shadow 0.2s; }
    .dark .prompt-input { background-color: #374151; border-color: #4b5563; }
    .prompt-input:focus { outline: none; border-color: var(--indigo-600); box-shadow: 0 0 0 1px var(--indigo-600); }
    
    .submit-btn { width: 100%; display: flex; justify-content: center; padding: 0.75rem 1rem; border: 1px solid transparent; border-radius: 0.5rem; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05); font-size: 0.875rem; font-weight: 500; color: white; background-color: var(--indigo-600); transition: background-color 0.3s; }
    .submit-btn:hover { background-color: var(--indigo-700); }
    .submit-btn:focus { outline: none; box-shadow: 0 0 0 2px var(--bg-card), 0 0 0 4px var(--indigo-600); }
    .submit-btn:disabled { background-color: var(--indigo-400); cursor: not-allowed; }
    .dark .submit-btn:disabled { background-color: var(--indigo-800); }
    
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .spinner { animation: spin 1s linear infinite; }
    .spinner-icon { height: 1.25rem; width: 1.25rem; margin-right: 0.75rem; }
    .error-msg { font-size: 0.875rem; color: #ef4444; text-align: center; }
    .dark .error-msg { color: #f87171; }
    
    .image-display-grid { display: grid; grid-template-columns: repeat(1, minmax(0, 1fr)); gap: 1.5rem; }
    @media (min-width: 768px) { .image-display-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 2rem; } }
    @media (min-width: 1024px) { .lg-col-span-3 { grid-column: span 3 / span 3; } }
    
    .result-container { display: flex; flex-direction: column; height: fit-content; }
    .result-title { font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem; text-align: center; color: var(--text-main); }
    @media (min-width: 640px) { .result-title { font-size: 1.75rem; } }
    
    .result-image-box { width: 100%; background-color: var(--bg-card); border-radius: 1rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); display: flex; align-items: center; justify-content: center; overflow: hidden; min-height: 400px; }
    @media (min-width: 768px) { .result-image-box { min-height: 500px; } }
    @media (min-width: 1024px) { .result-image-box { min-height: 600px; } }
    
    .result-image { width: 100%; height: 100%; object-fit: contain; max-height: 80vh; }
    
    .result-placeholder { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
    .result-placeholder-content { text-align: center; color: var(--gray-400); padding: 2rem; }
    .result-placeholder-icon { width: 4rem; height: 4rem; margin: 0 auto 1rem auto; }
    .result-placeholder-text { font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem; }
    .result-placeholder-hint { font-size: 0.875rem; opacity: 0.8; }
    
    .image-container { display: flex; flex-direction: column; align-items: center; }
    .image-title { font-size: 1.125rem; font-weight: 600; margin-bottom: 0.75rem; }
    .image-box { aspect-ratio: 1 / 1; width: 100%; background-color: var(--bg-card); border-radius: 1rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .image-box img { width: 100%; height: 100%; object-fit: contain; }
    .placeholder-text { text-align: center; color: var(--gray-400); padding: 1rem; }
    .loading-spinner-box { display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--gray-500); }
    .loading-spinner { height: 2.5rem; width: 2.5rem; margin-bottom: 0.5rem; }
    
    .gallery { margin-top: 3rem; }
    @media (min-width: 768px) { .gallery { margin-top: 4rem; } }
    .gallery-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 1.5rem; text-align: center; }
    @media (min-width: 640px) { .gallery-title { font-size: 1.5rem; } }

    .gallery-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.5rem; }
    @media (min-width: 640px) { .gallery-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
    @media (min-width: 768px) { .gallery-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); } }
    @media (min-width: 1024px) { .gallery-grid { grid-template-columns: repeat(6, minmax(0, 1fr)); } }
    @media (min-width: 1280px) { .gallery-grid { grid-template-columns: repeat(8, minmax(0, 1fr)); } }

    .gallery-item { aspect-ratio: 1 / 1; background-color: var(--bg-card); border-radius: 0.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); overflow: hidden; }
    .gallery-item img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }
    .gallery-item:hover img { transform: scale(1.05); }
    
    .footer { text-align: center; margin-top: 3rem; padding: 1.5rem 0; border-top: 1px solid var(--border-main); }
    @media (min-width: 768px) { .footer { margin-top: 4rem; } }
    .footer-content { display: flex; align-items: center; justify-content: center; gap: 0.5rem; color: var(--gray-500); }
    .dark .footer-content { color: var(--gray-400); }
    .footer-logo { height: 1.5rem; width: 1.5rem; }

    .upload-area.dragging {
      border-color: var(--indigo-600);
      background-color: rgba(79, 70, 229, 0.1);
      transition: background-color 0.3s ease, border-color 0.3s ease;
    }

    .upload-area.dragging .upload-icon {
      color: var(--indigo-600);
      transform: scale(1.1);
      transition: transform 0.3s ease, color 0.3s ease;
    }

    .upload-area.has-image.dragging .upload-overlay {
      opacity: 1;
      background-color: rgba(79, 70, 229, 0.8);
    }
  `;

  return (
    <>
      <style>{styles}</style>
      <div className="app-container">
        <div className="container">
          <header className="header">
            <div className="logo-container">
              <MirageLogo className="logo" />
              <span className="logo-subtitle hidden-sm">The AI Photo Editor</span>
            </div>
            <button onClick={toggleTheme} className="theme-toggle">
              {theme === 'dark' ? <SunIcon className="icon-size" /> : <MoonIcon className="icon-size" />}
            </button>
          </header>

          <main>
            <div className="main-grid">
              <div className="control-panel lg-col-span-2">
                <h2 className="panel-title">Edit Your Image</h2>
                <p className="panel-subtitle">Upload a photo and tell the AI what to change.</p>
                <form onSubmit={handleSubmit} className="form">
                  <div>
                    <label htmlFor="image-upload" className="form-label">
                      {originalImage ? "1. Uploaded Image (Click to change)" : "1. Upload Image"}
                    </label>
                    <div
                      className={`upload-area ${originalImage ? 'has-image' : ''}`}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      onClick={() => document.getElementById('image-upload').click()}
                    >
                      {originalImage ? (
                        <div className="uploaded-image-preview">
                          <img src={originalImage} alt="Uploaded preview" className="preview-image" />
                          <div className="upload-overlay">
                            <svg className="upload-icon-small" stroke="currentColor" fill="none" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <span className="upload-overlay-text">Click to change image</span>
                          </div>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                          <svg className="upload-icon" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          <div className="upload-text">
                            <span className="upload-browse">Upload a file</span>
                            <span style={{ paddingLeft: '0.25rem' }}>or drag and drop</span>
                          </div>
                          <p className="upload-hint">PNG, JPG, GIF up to 10MB</p>
                        </div>
                      )}
                      <input id="image-upload" name="image-upload" type="file" className="sr-only" accept="image/*" onChange={handleImageChange} />
                    </div>
                  </div>
                  <div>
                    <label htmlFor="prompt" className="form-label">2. Describe Your Edit</label>
                    <textarea id="prompt" rows="3" className="prompt-input" placeholder="e.g., 'Make the sky a vibrant sunset', 'Add a cute cat on the sofa'" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
                  </div>
                  <button type="submit" disabled={loading || !originalFile} className="submit-btn">
                    {loading ? (
                      <>
                        <svg className="spinner spinner-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle style={{opacity: 0.25}} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path style={{opacity: 0.75}} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </>
                    ) : "Generate Magic ✨"}
                  </button>
                  {error && <p className="error-msg">{error}</p>}
                </form>
              </div>

              <div className="lg-col-span-3">
                {originalImage && (
                  <div className="result-container">
                    <h3 className="result-title">✨ Generated Result</h3>
                    <div className="result-image-box">
                      {loading ? (
                        <div className="loading-spinner-box">
                          <svg className="spinner loading-spinner" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle style={{opacity: 0.25}} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path style={{opacity: 0.75}} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          <span>Brewing your image...</span>
                        </div>
                      ) : editedImage ? (
                        <img src={editedImage} alt="Edited result" className="result-image" />
                      ) : (
                        <div className="result-placeholder">
                          <div className="result-placeholder-content">
                            <svg className="result-placeholder-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            <p className="result-placeholder-text">Your masterpiece will appear here</p>
                            <p className="result-placeholder-hint">Add a prompt and click "Generate Magic" to start</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {gallery.length > 0 && (
              <div className="gallery">
                <h2 className="gallery-title">Your Creation Gallery</h2>
                <div className="gallery-grid">
                  {gallery.map((imgSrc, index) => (
                    <div key={index} className="gallery-item">
                      <img src={imgSrc} alt={`Gallery item ${index + 1}`} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </main>

          <footer className="footer">
            <div className="footer-content">
              <span>Made by</span>
              <IotaClusterLogo className="footer-logo" />
              <span>Iota Cluster</span>
            </div>
          </footer>
        </div>
      </div>
    </>
  );
}
