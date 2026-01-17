// Upload Document Modal Component
import { useState } from 'react'
import { motion } from 'framer-motion'
import { X, Upload, FileText } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

interface UploadDocumentModalProps {
    caseId: string
    clientId: string | null
    lawyerId: string
    caseNumber: string
    onClose: () => void
    onSuccess: () => void
}

export function UploadDocumentModal({
    caseId,
    clientId,
    lawyerId,
    caseNumber,
    onClose,
    onSuccess
}: UploadDocumentModalProps) {
    const [file, setFile] = useState<File | null>(null)
    const [documentType, setDocumentType] = useState('other')
    const [enableOCR, setEnableOCR] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [extracting, setExtracting] = useState(false)
    const [summarizing, setSummarizing] = useState(false)

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0])
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!file) {
            toast.error('يُرجى اختيار ملف')
            return
        }

        try {
            setUploading(true)

            // Create FormData
            const formData = new FormData()
            formData.append('file', file)
            formData.append('case_id', caseId)
            formData.append('client_id', clientId || '')
            formData.append('lawyer_id', lawyerId)
            formData.append('document_type', documentType)
            formData.append('enable_ocr', enableOCR.toString())

            // Upload document
            const uploadResponse = await axios.post(
                'http://localhost:8000/api/documents/upload',
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                }
            )

            const documentId = uploadResponse.data.document.id

            toast.success('تم رفع المستند بنجاح')

            // If OCR is enabled, trigger extraction
            if (enableOCR) {
                setExtracting(true)
                toast.info('جاري استخراج النص...')

                try {
                    const extractResponse = await axios.post(
                        `http://localhost:8000/api/documents/${documentId}/extract`
                    )

                    if (extractResponse.data.success) {
                        toast.success('تم استخراج النص بنجاح')

                        // Trigger summarization
                        setSummarizing(true)
                        setExtracting(false)
                        toast.info('جاري تلخيص المستند...')

                        const summarizeResponse = await axios.post(
                            `http://localhost:8000/api/documents/${documentId}/summarize`
                        )

                        if (summarizeResponse.data.success) {
                            toast.success('تم تلخيص المستند بنجاح')
                        }
                    }
                } catch (error: any) {
                    console.error('OCR/Summarization error:', error)
                    toast.error(error.response?.data?.detail || 'فشل معالجة المستند')
                } finally {
                    setExtracting(false)
                    setSummarizing(false)
                }
            }

            onSuccess()
        } catch (error: any) {
            console.error('Upload error:', error)
            toast.error(error.response?.data?.detail || 'فشل رفع المستند')
        } finally {
            setUploading(false)
        }
    }

    const isProcessing = uploading || extracting || summarizing

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-6 max-w-lg w-full"
            >
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            رفع مستند جديد
                        </h2>
                        <p className="text-gray-400 text-sm mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            القضية: {caseNumber}
                        </p>
                    </div>
                    <button onClick={onClose} disabled={isProcessing} className="text-gray-400 hover:text-white disabled:opacity-50">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* File Upload */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            الملف <span className="text-red-400">*</span>
                        </label>
                        <div className="relative">
                            <input
                                type="file"
                                onChange={handleFileChange}
                                accept=".pdf,.png,.jpg,.jpeg"
                                className="hidden"
                                id="file-upload"
                                disabled={isProcessing}
                            />
                            <label
                                htmlFor="file-upload"
                                className="flex items-center justify-center gap-2 w-full px-4 py-3 border-2 border-dashed border-gold-500/30 rounded-lg cursor-pointer hover:border-gold-500/50 transition bg-obsidian-900/30"
                            >
                                <Upload className="w-5 h-5 text-gold-500" />
                                <span className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {file ? file.name : 'اختر ملف (PDF, PNG, JPG)'}
                                </span>
                            </label>
                        </div>
                        {file && (
                            <p className="text-xs text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                الحجم: {(file.size / 1024).toFixed(2)} KB
                            </p>
                        )}
                    </div>

                    {/* Document Type */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            نوع المستند
                        </label>
                        <select
                            value={documentType}
                            onChange={(e) => setDocumentType(e.target.value)}
                            disabled={isProcessing}
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            <option value="other">أخرى</option>
                            <option value="contract">عقد</option>
                            <option value="court_document">مستند محكمة</option>
                            <option value="evidence">دليل</option>
                            <option value="power_of_attorney">توكيل</option>
                        </select>
                    </div>

                    {/* Enable OCR Checkbox */}
                    <div className="flex items-center gap-3 p-3 bg-obsidian-900/30 rounded-lg border border-gold-500/10">
                        <input
                            type="checkbox"
                            id="enable-ocr"
                            checked={enableOCR}
                            onChange={(e) => setEnableOCR(e.target.checked)}
                            disabled={isProcessing}
                            className="w-4 h-4 rounded border-gold-500/30 bg-obsidian-900 text-gold-500 focus:ring-gold-500"
                        />
                        <label htmlFor="enable-ocr" className="flex-1 text-white text-sm cursor-pointer" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="font-medium">تفعيل استخراج النص (OCR)</span>
                            <p className="text-xs text-gray-400 mt-1">
                                استخراج النص من المستند وتلخيصه تلقائياً باستخدام AI
                            </p>
                        </label>
                    </div>

                    {/* Progress Indicator */}
                    {isProcessing && (
                        <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                            <div className="flex items-center gap-3">
                                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                                <p className="text-blue-400 text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {uploading && 'جاري رفع الملف...'}
                                    {extracting && 'جاري استخراج النص...'}
                                    {summarizing && 'جاري التلخيص...'}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Buttons */}
                    <div className="flex gap-3 pt-4">
                        <button
                            type="submit"
                            disabled={!file || isProcessing}
                            className="flex-1 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all disabled:opacity-50"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            {uploading ? 'جاري الرفع...' : 'رفع المستند'}
                        </button>
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={isProcessing}
                            className="px-6 py-3 bg-obsidian-700 text-white font-medium rounded-lg hover:bg-obsidian-600 transition-colors disabled:opacity-50"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            إلغاء
                        </button>
                    </div>
                </form>
            </motion.div>
        </div>
    )
}
