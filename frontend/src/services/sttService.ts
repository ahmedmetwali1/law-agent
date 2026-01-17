/**
 * Speech-to-Text Service
 * Secure implementation using backend proxy
 */

export interface TranscriptionResponse {
    text: string;
}

export class STTService {
    /**
     * Transcribe audio blob to text via secure backend proxy
     */
    static async transcribe(audioBlob: Blob): Promise<string> {
        try {
            const formData = new FormData();
            formData.append('file', audioBlob, 'audio.webm');

            // Call backend proxy (credentials hidden server-side)
            const token = localStorage.getItem('access_token');

            // Validate token exists
            if (!token) {
                throw new Error('يجب تسجيل الدخول أولاً لاستخدام التسجيل الصوتي');
            }

            const response = await fetch('http://localhost:8000/api/transcribe', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`STT API returned ${response.status}: ${errorText}`);
            }

            const data: TranscriptionResponse = await response.json();
            return data.text || '';
        } catch (error) {
            console.error('STT transcription failed:', error);
            throw new Error('فشل في تحويل الصوت إلى نص. تأكد من الاتصال بالإنترنت.');
        }
    }
}
