chrome.runtime.onInstalled.addListener(() => {
    // Create context menu item
    chrome.contextMenus.create({
      id: "saveToKnowledgeBase",
      title: "Save to Knowledge Base",
      contexts: ["selection", "image"] // text or image
    });
  });
  
  // Listen for context menu clicks
  chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId === "saveToKnowledgeBase") {
      // Send message to content script
      const response = await chrome.tabs.sendMessage(tab.id, {
        type: "SAVE_HIGHLIGHT",
        payload: info
      });
      console.log("Response from content:", response);
    }
  });
  