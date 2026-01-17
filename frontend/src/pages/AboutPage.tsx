import { motion } from 'framer-motion'
import { Building2, Users, Shield, Target } from 'lucide-react'

export function AboutPage() {
    return (
        <div className="max-w-4xl mx-auto p-8">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-12"
            >
                <h1 className="text-4xl font-bold bg-gradient-to-r from-gold-400 via-gold-200 to-gold-500 bg-clip-text text-transparent mb-4 font-cairo">
                    من نحن
                </h1>
                <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                    نحن رواد التحول الرقمي في المجال القانوني، نسعى لتمكين المحامين بأحدث أدوات الذكاء الاصطناعي.
                </p>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-6">
                <div className="glass-card p-6">
                    <Building2 className="w-10 h-10 text-gold-500 mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">رؤيتنا</h3>
                    <p className="text-gray-400 leading-relaxed">
                        بناء المستقبل الرقمي لمهنة المحاماة من خلال توفير مساعد ذكي ومتكامل يدير كافة تفاصيل المكتب بدقة وكفاءة عالية.
                    </p>
                </div>

                <div className="glass-card p-6">
                    <Target className="w-10 h-10 text-blue-500 mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">مهمتنا</h3>
                    <p className="text-gray-400 leading-relaxed">
                        توفير الوقت والجهد للمحامي ليتفرغ للإبداع في عمله القانوني، بينما يتولى نظامنا إدارة المهام الروتينية والتحليل الأولي.
                    </p>
                </div>

                <div className="glass-card p-6">
                    <Shield className="w-10 h-10 text-green-500 mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">قيمنا</h3>
                    <p className="text-gray-400 leading-relaxed">
                        السرية المطلقة للبيانات، الدقة في الأداء، والشفافية التامة مع عملائنا هي الركائز الأساسية لكل ما نقوم به.
                    </p>
                </div>

                <div className="glass-card p-6">
                    <Users className="w-10 h-10 text-purple-500 mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">فريقنا</h3>
                    <p className="text-gray-400 leading-relaxed">
                        نخبة من الخبراء في القانون والتقنية والذكاء الاصطناعي يعملون معاً لتقديم تجربة مستخدم استثنائية.
                    </p>
                </div>
            </div>
        </div>
    )
}
