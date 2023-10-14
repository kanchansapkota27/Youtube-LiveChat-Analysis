import React, { useEffect, useState,useRef } from 'react';
import VideoMessage from './VideoMessage'; // Import your VideoMessage component
import { useViewer } from '../contexts/ViewerContext';

const MAX_MESSAGES = 150; // Maximum number of messages to display

const SSEListener = () => {
  const [messages, setMessages] = useState([]);
  const messagesContainerRef = useRef(null);

  const {setViewerCount,setIsLive,video,setVideo}=useViewer()

  useEffect(() => {
    const eventSource = new EventSource('http://localhost:3000/stream');

    eventSource.onmessage = (event) => {
        const rawData=event.data;
        // const validJSONData = rawData.replace(/'/g, '"').replace(/True/g, 'true');
        const validJSONData = rawData
  .replace(/'/g, '"')
  .replace(/True/g, 'true')
  .replace(/False/g, 'false');
      const eventData = JSON.parse(validJSONData);
      if(video==null){
        // setVideo(`https://www.youtube.com/watch?v=${eventData.video_id}`)
        setVideo(eventData.video_id)
      }
      setViewerCount(eventData?.viewers_count)
      setIsLive(eventSource?.is_live)

      // Update messages array while maintaining the maximum limit
      // setMessages((prevMessages) => {
      //   const newMessages = [eventData, ...prevMessages].slice(0, MAX_MESSAGES);
      //   return newMessages;
      // });

      setMessages((prevMessages) => {
        const newMessages = [...prevMessages, eventData].slice(-MAX_MESSAGES);
        return newMessages;
      });

    };

    

    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  useEffect(() => {
    // Scroll to the bottom when messages change
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div ref={messagesContainerRef} className='h-full overflow-y-auto py-10'>
      {messages.map((message, index) => (
        <VideoMessage key={index} data={message} />
      ))}
    </div>
  );
};

export default SSEListener;
