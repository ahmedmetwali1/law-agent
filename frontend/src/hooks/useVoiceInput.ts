import { useState, useRef, useCallback } from 'react';
import { STTService } from '../services/sttService';

export function useVoiceInput() {
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    const startRecording = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Use webm format with opus codec for best compatibility
            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            chunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            mediaRecorder.start();
            mediaRecorderRef.current = mediaRecorder;
            setIsRecording(true);
        } catch (error) {
            console.error('Failed to start recording:', error);
            throw new Error('فشل في الوصول إلى الميكروفون. تأكد من السماح بالوصول.');
        }
    }, []);

    const stopRecording = useCallback((): Promise<string> => {
        return new Promise((resolve, reject) => {
            const mediaRecorder = mediaRecorderRef.current;

            if (!mediaRecorder || mediaRecorder.state === 'inactive') {
                reject(new Error('لا يوجد تسجيل نشط'));
                return;
            }

            mediaRecorder.onstop = async () => {
                setIsRecording(false);
                setIsProcessing(true);

                try {
                    // Create blob from chunks
                    const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });

                    // Stop all tracks
                    mediaRecorder.stream.getTracks().forEach(track => track.stop());

                    // Transcribe
                    const text = await STTService.transcribe(audioBlob);

                    setIsProcessing(false);
                    resolve(text);
                } catch (error) {
                    setIsProcessing(false);
                    reject(error);
                }
            };

            mediaRecorder.stop();
        });
    }, []);

    const cancelRecording = useCallback(() => {
        const mediaRecorder = mediaRecorderRef.current;

        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }

        chunksRef.current = [];
        setIsRecording(false);
        setIsProcessing(false);
    }, []);

    return {
        isRecording,
        isProcessing,
        startRecording,
        stopRecording,
        cancelRecording,
    };
}
