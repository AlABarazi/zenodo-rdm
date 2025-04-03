
// Function to replace the PDF manifest with our custom manifest
function replacePDFManifest() {
  // The manifest data
  const customManifest = {
  "@context": "http://iiif.io/api/presentation/2/context.json",
  "@type": "sc:Manifest",
  "@id": "https://127.0.0.1:5000/api/iiif/record:216/manifest",
  "label": "PDF Document",
  "metadata": [
    {
      "label": "Publication Date",
      "value": "2025-04-03"
    }
  ],
  "description": "Manifest generated for PDF document",
  "sequences": [
    {
      "@id": "https://127.0.0.1:5000/api/iiif/record:216/sequence/default",
      "@type": "sc:Sequence",
      "label": "Current Page Order",
      "viewingDirection": "left-to-right",
      "viewingHint": "individuals",
      "canvases": [
        {
          "@id": "https://127.0.0.1:5000/api/iiif/record:216/canvas/history00871.pdf.ptif",
          "@type": "sc:Canvas",
          "label": "Page from history00871.pdf.ptif",
          "width": 1911,
          "height": 2760,
          "images": [
            {
              "@id": "https://127.0.0.1:5000/api/iiif/record:216/canvas/history00871.pdf.ptif/image",
              "@type": "oa:Annotation",
              "motivation": "sc:painting",
              "resource": {
                "@id": "https://127.0.0.1:5000/api/iiif/21/6_/_/history00871.pdf.ptif/full/full/0/default.jpg",
                "@type": "dctypes:Image",
                "format": "image/jpeg",
                "width": 1911,
                "height": 2760,
                "service": {
                  "@id": "https://127.0.0.1:5000/api/iiif/21/6_/_/history00871.pdf.ptif",
                  "@context": "http://iiif.io/api/image/2/context.json",
                  "profile": "http://iiif.io/api/image/2/level1.json"
                }
              },
              "on": "https://127.0.0.1:5000/api/iiif/record:216/canvas/history00871.pdf.ptif"
            }
          ]
        },
        {
          "@id": "https://127.0.0.1:5000/api/iiif/record:216/canvas/history00871.pdf.ptif",
          "@type": "sc:Canvas",
          "label": "Page from history00871.pdf.ptif",
          "width": 1911,
          "height": 2760,
          "images": [
            {
              "@id": "https://127.0.0.1:5000/api/iiif/record:216/canvas/history00871.pdf.ptif/image",
              "@type": "oa:Annotation",
              "motivation": "sc:painting",
              "resource": {
                "@id": "https://127.0.0.1:5000/api/iiif/20/6_/_/history00871.pdf.ptif/full/full/0/default.jpg",
                "@type": "dctypes:Image",
                "format": "image/jpeg",
                "width": 1911,
                "height": 2760,
                "service": {
                  "@id": "https://127.0.0.1:5000/api/iiif/20/6_/_/history00871.pdf.ptif",
                  "@context": "http://iiif.io/api/image/2/context.json",
                  "profile": "http://iiif.io/api/image/2/level1.json"
                }
              },
              "on": "https://127.0.0.1:5000/api/iiif/record:216/canvas/history00871.pdf.ptif"
            }
          ]
        }
      ]
    }
  ]
};
  
  // Find the Mirador instance
  const miradorInstanceElement = document.getElementById('m3-dist');
  if (!miradorInstanceElement) {
    console.error('Mirador instance not found');
    return;
  }
  
  // Get the manifest URL from the data attribute
  const manifestUrl = miradorInstanceElement.getAttribute('data-manifest');
  console.log('Manifest URL:', manifestUrl);
  
  // Create a new manifest URL using the same URL but with a timestamp to bypass cache
  const newManifestUrl = manifestUrl + '?t=' + Date.now();
  
  // Override the fetch function to return our custom manifest for the manifest URL
  const originalFetch = window.fetch;
  window.fetch = function(url, options) {
    if (url.startsWith(manifestUrl)) {
      console.log('Intercepting fetch request for manifest URL:', url);
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(customManifest)
      });
    }
    return originalFetch(url, options);
  };
  
  // Set the new manifest URL and trigger a reload
  miradorInstanceElement.setAttribute('data-manifest', newManifestUrl);
  
  // Create a new event to trigger a reload
  const event = new Event('manifestChanged');
  miradorInstanceElement.dispatchEvent(event);
  
  console.log('Manifest replaced successfully');
}

// Run the function
replacePDFManifest();
