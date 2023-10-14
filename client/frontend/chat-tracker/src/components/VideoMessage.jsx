// VideoMessage.js
import React from "react";
import Avatar from "react-avatar";

function VideoMessage({ data }) {

  function formatDateToLocalTime(dateString) {
    const dateObject = new Date(dateString);
    const options = { 
      // timeZoneName: 'short', 
      hour: "2-digit", minute: "2-digit"};
    const localDate = dateObject.toLocaleDateString(undefined, options);
    const localTime = dateObject.toLocaleTimeString(undefined, options);
    return `${localTime}`;
  }

  const {
    message_author_name,
    message_dt,
    message_content,
    inferred_sentiment,
  } = data;

  // Function to format the timestamp to local time

  return (
    <div
      className={`${inferred_sentiment === "NEG"
          ? "bg-red-200"
          : inferred_sentiment === "POS"
            ? "bg-green-200"
            : "bg-blue-200"
        }  rounded-lg p-2 shadow-md my-1 text-gray-800 text-xs`}
    >
      {/* <div className="flex justify-between">
        
        <div className="font-semibold">{message_author_name}</div>
        <div className="text-right text-gray-600">
          {formatDateToLocalTime(message_dt)}
        </div>
      </div>
      <div className="mt-2">{message_content}</div> */}
      <div className="flex justify-between space-x-2 items-center space-y-1">
        <Avatar className="flex" name={message_author_name} round size="30"/>
        <div className="flex flex-1 gap-2 flex-wrap">
        <span className="text-gray-600">{formatDateToLocalTime(message_dt)}</span>
        <span className="text-gray-800 font-semibold">{message_author_name}</span>
        <span className="text-gray-700 ">{message_content}</span>
        </div>
      </div>
    </div>
  );
}

export default VideoMessage;
