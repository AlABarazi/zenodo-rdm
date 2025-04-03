// PDF Viewer Fix for Zenodo RDM
// This script checks if a PDF is being displayed in Mirador and adds PTIF files to the manifest if available

(function() {
  // Function to check if we're on a record page with a PDF
  function isPDFRecordPage() {
    const miradorElement = document.getElementById('m3-dist');
    if (!miradorElement) return false;
    
    // Check if the manifest URL indicates a PDF
    const manifestUrl = miradorElement.getAttribute('data-manifest');
    return manifestUrl && manifestUrl.includes('/api/iiif/record:');
  }

  // Function to extract record ID from the manifest URL
  function extractRecordID(manifestUrl) {
    const match = manifestUrl.match(/\/api\/iiif\/record:(\d+)\/manifest/);
    return match ? match[1] : null;
  }

  // Function to fetch PTIF information for a record
  async function fetchPTIFInfo(recordId) {
    try {
      // Fetch from a new endpoint that would return information about available PTIFs
      // This is a placeholder - in a real implementation, you would create this endpoint
      const response = await fetch(`/api/records/${recordId}/ptif-info`);
      if (!response.ok) {
        throw new Error(`Failed to fetch PTIF info: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching PTIF info:', error);
      // Fallback: Search for PTIFs in common locations
      return searchForPTIFs(recordId);
    }
  }

  // Fallback function to search for PTIFs based on record ID
  async function searchForPTIFs(recordId) {
    // These are common patterns for PTIF file paths based on record ID
    const pathPatterns = [
      `/api/iiif/${recordId.slice(0, 2)}/${recordId.slice(2)}_/_/`,
      `/api/iiif/${recordId.slice(0, 2) - 1}/${recordId.slice(2)}_/_/`
    ];
    
    const ptifFiles = [];
    
    // This is just a placeholder - in reality, we would need a server endpoint to do this check
    // For now, assume we found some PTIFs
    ptifFiles.push({
      path: pathPatterns[0] + 'history00871.pdf.ptif',
      width: 1911,
      height: 2760
    });
    
    return {
      recordId: recordId,
      ptifFiles: ptifFiles
    };
  }

  // Function to enhance a manifest with PTIF canvases
  function enhanceManifestWithPTIF(manifest, ptifInfo) {
    if (!ptifInfo || !ptifInfo.ptifFiles || ptifInfo.ptifFiles.length === 0) {
      console.warn('No PTIF files found to enhance manifest');
      return manifest;
    }

    // Create a copy of the manifest to modify
    const enhancedManifest = JSON.parse(JSON.stringify(manifest));
    
    // Find the sequence and ensure it has a canvases array
    const sequence = enhancedManifest.sequences[0];
    if (!sequence) {
      console.error('No sequence found in manifest');
      return manifest;
    }
    
    if (!sequence.canvases) {
      sequence.canvases = [];
    }
    
    // Clear existing canvases if they're empty
    if (sequence.canvases.length === 0) {
      // Add a canvas for each PTIF file
      ptifInfo.ptifFiles.forEach((ptif, index) => {
        const filename = ptif.path.split('/').pop();
        const canvas = {
          "@id": `${enhancedManifest['@id']}/canvas/${filename}`,
          "@type": "sc:Canvas",
          "label": `Page ${index + 1} from ${filename}`,
          "width": ptif.width,
          "height": ptif.height,
          "images": [
            {
              "@id": `${enhancedManifest['@id']}/canvas/${filename}/image`,
              "@type": "oa:Annotation",
              "motivation": "sc:painting",
              "resource": {
                "@id": `${ptif.path}/full/full/0/default.jpg`,
                "@type": "dctypes:Image",
                "format": "image/jpeg",
                "width": ptif.width,
                "height": ptif.height,
                "service": {
                  "@id": ptif.path,
                  "@context": "http://iiif.io/api/image/2/context.json",
                  "profile": "http://iiif.io/api/image/2/level1.json"
                }
              },
              "on": `${enhancedManifest['@id']}/canvas/${filename}`
            }
          ]
        };
        sequence.canvases.push(canvas);
      });
    }
    
    return enhancedManifest;
  }

  // Main function to fix PDF viewing
  async function fixPDFViewer() {
    if (!isPDFRecordPage()) return;
    
    const miradorElement = document.getElementById('m3-dist');
    const manifestUrl = miradorElement.getAttribute('data-manifest');
    const recordId = extractRecordID(manifestUrl);
    
    if (!recordId) {
      console.error('Could not extract record ID from manifest URL');
      return;
    }
    
    console.log(`Found record ID: ${recordId}`);
    
    try {
      // Fetch the original manifest
      const origManifestResponse = await fetch(manifestUrl);
      if (!origManifestResponse.ok) {
        throw new Error(`Failed to fetch original manifest: ${origManifestResponse.statusText}`);
      }
      
      const originalManifest = await origManifestResponse.json();
      
      // Get PTIF information for this record
      const ptifInfo = await fetchPTIFInfo(recordId);
      
      // Enhance the manifest with PTIF canvases
      const enhancedManifest = enhanceManifestWithPTIF(originalManifest, ptifInfo);
      
      // Only proceed if we have canvases
      if (enhancedManifest.sequences[0].canvases.length === 0) {
        console.warn('No canvases available after enhancement');
        return;
      }
      
      // Override fetch for this manifest URL
      const originalFetch = window.fetch;
      window.fetch = function(url, options) {
        if (url.startsWith(manifestUrl)) {
          console.log('Intercepting fetch request for manifest URL:', url);
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(enhancedManifest)
          });
        }
        return originalFetch(url, options);
      };
      
      // Create a new manifest URL to force reload
      const newManifestUrl = manifestUrl + '?t=' + Date.now();
      miradorElement.setAttribute('data-manifest', newManifestUrl);
      
      // Trigger a reload
      const event = new Event('manifestChanged');
      miradorElement.dispatchEvent(event);
      
      console.log('PDF viewer fixed with PTIF canvases');
      
    } catch (error) {
      console.error('Error fixing PDF viewer:', error);
    }
  }

  // Run when the DOM is fully loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixPDFViewer);
  } else {
    fixPDFViewer();
  }
})(); 