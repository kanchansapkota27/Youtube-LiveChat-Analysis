// ViewerContext.js
import React, { createContext, useContext, useEffect, useState } from "react";

// Create a context
const ViewerContext = createContext();

// Create a provider component
export function ViewerProvider({ children }) {
  const [viewerCount, setViewerCount] = useState(0);
  const [isLive, setIsLive] = useState(false);
  const [video,setVideo]=useState(null)
  const [videoDetails,setVideoDetails]=useState({})

  // You can add functions to update viewerCount and isLive here if needed.
  


  return (
    <ViewerContext.Provider value={{ viewerCount,setViewerCount,setIsLive,isLive,video,setVideo,videoDetails,setVideoDetails}}>
      {children}
    </ViewerContext.Provider>
  );
}

// Create a custom hook to access the context
export function useViewer() {
  const context = useContext(ViewerContext);
  if (!context) {
    throw new Error("useViewer must be used within a ViewerProvider");
  }
  return context;
}
