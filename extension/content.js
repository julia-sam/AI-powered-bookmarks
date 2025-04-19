// Listen for messages from background.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "SAVE_HIGHLIGHT") {
      const { payload } = request;
  
      let selectedText = "";
      let pageUrl = window.location.href;
      let pageTitle = document.title;
  
      // For text selection
      if (payload.selectionText) {
        selectedText = payload.selectionText;
      }
  
      // For images
      if (payload.mediaType === "image") {
        // You might store the image URL, or do something else
        selectedText = payload.srcUrl;
      }
  
      // Now send data to your Flask backend
      fetch("http://localhost:5000/save_entry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: selectedText,
          page_url: pageUrl,
          page_title: pageTitle,
          timestamp: new Date().toISOString()
        })
      })
        .then(res => res.json())
        .then(data => {
          console.log("Server response:", data);
          sendResponse({ success: true, data });
        })
        .catch(err => {
          console.error(err);
          sendResponse({ success: false, error: err });
        });
  
      // Return true to indicate async response
      return true;
    }
  });
  