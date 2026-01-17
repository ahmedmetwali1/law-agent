import { motion } from 'framer-motion'
import { Lock, Eye, Database, FileCheck } from 'lucide-react'

export function PrivacyPage() {
    return (
        <div className="max-w-4xl mx-auto p-8">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-12"
            >
                <h1 className="text-4xl font-bold bg-gradient-to-r from-gold-400 via-gold-200 to-gold-500 bg-clip-text text-transparent mb-6 font-cairo text-center">
                    سياسة الخصوصية
                </h1>

                <div className="space-y-8 text-gray-300 leading-relaxed">
                    <section className="glass-card p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <Lock className="w-6 h-6 text-gold-500" />
                            <h2 className="text-xl font-bold text-white">حماية البيانات والسرية</h2>
                        </div>
                        <p>
                            نحن ندرك حساسية المعلومات القانونية. جميع البيانات مشفرة باستخدام أحدث تقنيات التشفير (AES-256) ولا يتم مشاركتها مع أي طرف ثالث. بيانات موكليك وقضاياك هي ملك لك وحدك.
                        </p>
                    </section>

                    <section className="glass-card p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <Database className="w-6 h-6 text-blue-500" />
                            <h2 className="text-xl font-bold text-white">تخزين ومعالجة البيانات</h2>
                        </div>
                        <p>
                            يتم تخزين البيانات في خوادم آمنة ومتوافقة مع المعايير الدولية. عند استخدام ميزات الذكاء الاصطناعي، يتم معالجة البيانات بشكل آني دون تخزينها لأغراض التدريب، لضمان الخصوصية التامة.
                        </p>
                    </section>

                    <section className="glass-card p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <Eye className="w-6 h-6 text-green-500" />
                            <h2 className="text-xl font-bold text-white">حقوق الوصول والتحكم</h2>
                        </div>
                        <p>
                            أنت المتحكم الوحيد في بياناتك. يمكنك طلب نسخة كاملة من بياناتك أو حذفها نهائياً من نظامنا في أي وقت من خلال إعدادات الحساب.
                        </p>
                    </section>
                </div>
            </motion.div>
        </div>
    )
}
