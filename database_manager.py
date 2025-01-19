import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class Video:
    BV: str
    title: Optional[str] = None
    duration: Optional[int] = None
    audio_path: Optional[str] = None
    srt_path: Optional[str] = None
    download_date: Optional[datetime] = None
    status: int = 0
    notes: Optional[str] = None
    id: Optional[int] = None

class VideoDatabase:
    def __init__(self, db_path="videos.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_table()
    
    def create_table(self):
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            BV TEXT NOT NULL,           -- Bilibili BV号
            title TEXT,
            duration INTEGER,           -- 视频时长(秒)
            audio_path TEXT,            -- 音频文件路径
            srt_path TEXT,              -- 视频文件路径
            download_date TIMESTAMP,
            status INTEGER DEFAULT 0,    -- 状态(0:未下载, 1:已下载音频, 2: 已转换成 srt)
            notes TEXT                  -- 备注信息
        )
        ''')
        self.conn.commit()
    
    def _row_to_video(self, row) -> Optional[Video]:
        if row is None:
            return None
        return Video(
            id=row[0],
            BV=row[1],
            title=row[2],
            duration=row[3],
            audio_path=row[4],
            srt_path=row[5],
            download_date=datetime.fromisoformat(row[6]) if row[6] else None,
            status=row[7],
            notes=row[8]
        )
    
    def add_bv(self, BV):
        # First check if BV exists
        cursor = self.conn.execute('SELECT id FROM videos WHERE BV = ?', (BV,))
        if cursor.fetchone() is not None:
            return False

        # If BV doesn't exist, insert it
        sql = '''
        INSERT INTO videos (BV) VALUES (?)
        '''
        self.conn.execute(sql, (BV,))
        self.conn.commit()
        return True  # Successfully added new BV

    def update_video(self, video: Video) -> bool:
        if video.id is None:
            return False
            
        sql = '''
        UPDATE videos 
        SET title=?, duration=?, audio_path=?, srt_path=?, download_date=?, status=?, notes=?
        WHERE id=?
        '''
        self.conn.execute(sql, (
            video.title,
            video.duration,
            video.audio_path,
            video.srt_path,
            video.download_date.isoformat() if video.download_date else None,
            video.status,
            video.notes,
            video.id
        ))
        self.conn.commit()
        return True
    
    def get_video_by_bv(self, bv: str) -> list[Video]:
        cursor = self.conn.execute(
            'SELECT * FROM videos WHERE bv LIKE ?', 
            (f'%{bv}%',)
        )
        return [self._row_to_video(row) for row in cursor.fetchall()]
    
    def get_all_no_audio_videos(self) -> list[Video]:
        cursor = self.conn.execute(
            'SELECT * FROM videos WHERE status = 0'
        )
        return [self._row_to_video(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()