import React, { useRef, useEffect } from 'react';

const AudioPlayer = ({ src, autoPlay }) => {
  const audioRef = useRef(null);
  
  useEffect(() => {
    if (autoPlay && audioRef.current && src) {
      audioRef.current.play().catch(error => {
        console.error('Auto-play failed:', error);
      });
    }
  }, [src, autoPlay]);

  return (
    <div className="audio-player-wrapper">
      {src && (
        <audio 
          ref={audioRef}
          src={src}
          controls
          className="audio-player"
        />
      )}
    </div>
  );
};

export default AudioPlayer;