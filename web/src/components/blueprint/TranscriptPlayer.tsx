/**
 * Transcript Player Component - Phase 8
 * Displays transcript with behavior highlights and timing
 */

import { useState, useRef, useEffect } from 'react';
import { Play, Pause, SkipForward, SkipBack } from 'lucide-react';

interface TranscriptSegment {
  speaker: string;
  text: string;
  start: number;
  end: number;
  confidence?: number;
}

interface BehaviorMatch {
  behavior_id: string;
  behavior_name: string;
  matched_text: string;
  start_time: number;
  end_time: number;
  confidence: number;
  violation?: boolean;
}

interface TranscriptPlayerProps {
  segments: TranscriptSegment[];
  behaviorMatches?: BehaviorMatch[];
  onTimeUpdate?: (time: number) => void;
}

export default function TranscriptPlayer({
  segments,
  behaviorMatches = [],
  onTimeUpdate
}: TranscriptPlayerProps) {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = setInterval(() => {
        setCurrentTime((prev) => {
          const newTime = prev + 0.1 * playbackRate;
          if (onTimeUpdate) {
            onTimeUpdate(newTime);
          }
          return newTime;
        });
      }, 100);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, playbackRate, onTimeUpdate]);

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const seek = (seconds: number) => {
    setCurrentTime(Math.max(0, Math.min(getTotalDuration(), currentTime + seconds)));
  };

  const getTotalDuration = () => {
    if (segments.length === 0) return 0;
    return Math.max(...segments.map(s => s.end || s.start + 5));
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getMatchesForSegment = (segment: TranscriptSegment): BehaviorMatch[] => {
    return behaviorMatches.filter(match => 
      match.start_time >= segment.start && match.start_time <= segment.end
    );
  };

  const highlightText = (text: string, matches: BehaviorMatch[]): React.ReactNode => {
    if (matches.length === 0) return text;

    // Simple highlighting - in production would use more sophisticated text matching
    let result: React.ReactNode[] = [];
    let lastIndex = 0;

    matches.forEach((match, index) => {
      const matchText = match.matched_text.toLowerCase();
      const textLower = text.toLowerCase();
      const matchIndex = textLower.indexOf(matchText, lastIndex);

      if (matchIndex >= 0) {
        // Add text before match
        if (matchIndex > lastIndex) {
          result.push(text.substring(lastIndex, matchIndex));
        }

        // Add highlighted match
        result.push(
          <span
            key={`match-${index}`}
            className={`px-1 rounded ${
              match.violation
                ? 'bg-red-200 text-red-900'
                : 'bg-green-200 text-green-900'
            }`}
            title={`${match.behavior_name} (${(match.confidence * 100).toFixed(0)}% confidence)`}
          >
            {text.substring(matchIndex, matchIndex + match.matched_text.length)}
          </span>
        );

        lastIndex = matchIndex + match.matched_text.length;
      }
    });

    // Add remaining text
    if (lastIndex < text.length) {
      result.push(text.substring(lastIndex));
    }

    return result.length > 0 ? result : text;
  };

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* Controls */}
      <div className="border-b border-slate-200 dark:border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {isPlaying ? (
                <Pause className="w-5 h-5" />
              ) : (
                <Play className="w-5 h-5" />
              )}
            </button>
            <button
              onClick={() => seek(-5)}
              className="p-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              title="Rewind 5s"
            >
              <SkipBack className="w-5 h-5" />
            </button>
            <button
              onClick={() => seek(5)}
              className="p-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              title="Forward 5s"
            >
              <SkipForward className="w-5 h-5" />
            </button>
            <div className="text-sm text-slate-600 dark:text-slate-400">
              {formatTime(currentTime)} / {formatTime(getTotalDuration())}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-600 dark:text-slate-400">Speed:</label>
            <select
              value={playbackRate}
              onChange={(e) => setPlaybackRate(parseFloat(e.target.value))}
              className="px-2 py-1 border border-slate-300 dark:border-slate-600 rounded text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
            >
              <option value="0.5">0.5x</option>
              <option value="1">1x</option>
              <option value="1.5">1.5x</option>
              <option value="2">2x</option>
            </select>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
            <div
              className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all"
              style={{ width: `${(currentTime / getTotalDuration()) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Transcript */}
      <div
        ref={containerRef}
        className="p-6 max-h-96 overflow-y-auto space-y-3"
      >
        {segments.map((segment, index) => {
          const matches = getMatchesForSegment(segment);
          const isActive = currentTime >= segment.start && currentTime <= segment.end;
          const isPast = currentTime > segment.end;

          return (
            <div
              key={index}
              className={`p-3 rounded-lg border transition-colors ${
                isActive
                  ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-600'
                  : isPast
                  ? 'bg-slate-50 dark:bg-slate-700/50 border-slate-200 dark:border-slate-600'
                  : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <div
                    className={`w-2 h-2 rounded-full mt-2 ${
                      segment.speaker === 'agent'
                        ? 'bg-blue-600'
                        : 'bg-green-600'
                    }`}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-slate-900 dark:text-white">
                      {segment.speaker === 'agent' ? 'Agent' : 'Customer'}
                    </span>
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {formatTime(segment.start)} - {formatTime(segment.end)}
                    </span>
                    {matches.length > 0 && (
                      <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded">
                        {matches.length} match{matches.length !== 1 ? 'es' : ''}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-700 dark:text-slate-300">
                    {highlightText(segment.text, matches)}
                  </p>
                  {matches.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {matches.map((match, matchIndex) => (
                        <div
                          key={matchIndex}
                          className={`text-xs px-2 py-1 rounded ${
                            match.violation
                              ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                              : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                          }`}
                        >
                          {match.violation ? '⚠️' : '✓'} {match.behavior_name} ({(match.confidence * 100).toFixed(0)}%)
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="border-t border-slate-200 dark:border-slate-700 px-6 py-3 bg-slate-50 dark:bg-slate-700/50">
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-600 dark:bg-blue-500 rounded-full" />
            <span className="text-slate-600 dark:text-slate-400">Agent</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-600 dark:bg-green-500 rounded-full" />
            <span className="text-slate-600 dark:text-slate-400">Customer</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-green-200 dark:bg-green-900/30 text-green-900 dark:text-green-300 rounded">Match</span>
            <span className="text-slate-600 dark:text-slate-400">Behavior detected</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-red-200 dark:bg-red-900/30 text-red-900 dark:text-red-300 rounded">Violation</span>
            <span className="text-slate-600 dark:text-slate-400">Policy violation</span>
          </div>
        </div>
      </div>
    </div>
  );
}

