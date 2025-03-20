import os
import argparse
from datetime import datetime
from abc import ABC, abstractmethod
from database_manager import VideoDatabase, Video

def format_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

class WhisperBase(ABC):
    @abstractmethod
    def transcribe(self, audio_path):
        pass

    @abstractmethod
    def cleanup(self):
        pass

class OpenAIWhisper(WhisperBase):
    def __init__(self, model_size="large-v3"):
        import whisper
        import torch
        torch.set_num_threads(12)
        self.model = whisper.load_model(model_size)
    
    def transcribe(self, audio_path):
        result = self.model.transcribe(audio_path)
        # Convert OpenAI Whisper format to common format
        segments = []
        for segment in result["segments"]:
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip()
            })
        return segments
    
    def cleanup(self):
        # No cleanup needed for OpenAI Whisper
        pass

class FasterWhisper(WhisperBase):
    def __init__(self, model_size="large-v3"):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model_size, device="cpu")
    
    def transcribe(self, audio_path):
        segments, _ = self.model.transcribe(audio_path, beam_size=5)
        # Convert Faster Whisper format to common format
        return [{
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        } for segment in segments]
    
    def cleanup(self):
        # Clean up resources if needed
        if hasattr(self.model, 'cleanup'):
            self.model.cleanup()

def get_whisper_model(model_type="whisper", model_size="large-v3"):
    """Factory function to create appropriate Whisper model"""
    if model_type == "whisper":
        return OpenAIWhisper(model_size)
    elif model_type == "faster-whisper":
        return FasterWhisper(model_size)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

def generate_srt(model: WhisperBase, audio_path: str, output_path: str) -> bool:
    """
    Generate SRT file from audio using Whisper model
    Returns True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Transcribe audio
        segments = model.transcribe(audio_path)
        
        # Write SRT file
        with open(output_path, "w", encoding='utf-8') as srt_file:
            for i, segment in enumerate(segments, start=1):
                start_time = segment["start"]
                end_time = segment["end"]
                text = segment["text"]
                
                srt_file.write(f"{i}\n")
                srt_file.write(f"{format_time(start_time)} --> {format_time(end_time)}\n")
                srt_file.write(f"{text}\n\n")
        
        return True
    except Exception as e:
        print(f"Error generating SRT: {str(e)}")
        return False

def process_pending_videos(model_type="whisper", model_size="turbo", 
                         db_path="videos.db", srt_output_dir="data/srt"):
    """
    Process all videos with status=1 (audio downloaded) and generate SRT files
    """
    # Initialize database and model
    db = VideoDatabase()
    model = get_whisper_model(model_type, model_size)
    
    try:
        # Get all videos with downloaded audio (status=1)
        cursor = db.conn.execute('SELECT * FROM videos WHERE status = 1')
        pending_videos = [db._row_to_video(row) for row in cursor.fetchall()]
        
        print(f"Found {len(pending_videos)} videos to process")
        
        for video in pending_videos:
            if not video.audio_path or not os.path.exists(video.audio_path):
                print(f"Audio file not found for BV: {video.BV}")
                continue
                
            print(f"Processing BV: {video.BV}")
            
            # Generate SRT path
            srt_path = os.path.join(srt_output_dir, f"{video.BV}.srt")
            
            # Generate SRT file
            if generate_srt(model, video.audio_path, srt_path):
                # Update video status and path
                video.status = 2
                video.srt_path = srt_path
                video.notes = f"SRT generated on {datetime.now().isoformat()}"
                db.update_video(video)
                print(f"Successfully generated SRT for BV: {video.BV}")
            else:
                print(f"Failed to generate SRT for BV: {video.BV}")
    
    finally:
        model.cleanup()
        db.close()

def main():
    parser = argparse.ArgumentParser(description='Generate SRT files using Whisper')
    parser.add_argument('-m', '--model', choices=['whisper', 'faster-whisper'],
                      default='whisper', help='Whisper implementation to use')
    parser.add_argument('-s', '--model_size', 
                      default='turbo', help='Model size to use')
    
    args = parser.parse_args()
    process_pending_videos(args.model, args.model_size)

if __name__ == "__main__":
    main()