import { motion } from 'framer-motion'
import { Sparkles, Shield, Zap, Globe, Cpu, BarChart3, Users, Briefcase, Gavel, FileText, CheckSquare, Clock } from 'lucide-react'

export function ConceptPage() {
    const features = [
        {
            icon: Briefcase,
            title: "إدارة المكتب الشاملة",
            description: "نظام مركزي متكامل يتيح لك إدارة جميع جوانب مكتبك القانوني من منصة واحدة. وداعاً للأوراق المبعثرة والأنظمة المتعددة."
        },
        {
            icon: Users,
            title: "إدارة الموكلين الاحترافية",
            description: "سجل رقمي متكامل لكل موكل، يشمل بياناتهم، قضاياهم، مستنداتهم، وسجل التواصل. إضافة وتعديل البيانات بمرونة عالية."
        },
        {
            icon: BarChart3,
            title: "تقارير وتحليلات ذكية",
            description: "لوحات مؤشرات تفاعلية تعطيك رؤية شاملة عن أداء المكتب، القضايا الرابحة، وتوزيع المهام، مما يساعدك على اتخاذ قرارات مدروسة."
        },
        {
            icon: Gavel,
            title: "مراقبة الجلسات والقضايا",
            description: "تتبع دقيق لمواعيد الجلسات وتحديثات القضايا لحظة بلحظة. تنبيهات ذكية تضمن لك عدم تفويت أي موعد قانوني مهم."
        },
        {
            icon: CheckSquare,
            title: "إدارة المهام وفريق العمل",
            description: "نظام توزيع مهام متطور للمحامين والمساعدين. تابع سير العمل، ونسب الإنجاز، واضمن كفاءة الأداء التشغيلي لمكتبك."
        },
        {
            icon: FileText,
            title: "أتمتة المستندات والعقود",
            description: "أنشئ العقود والمذكرات القانونية في ثوانٍ باستخدام نماذج ذكية معتمدة، مع إمكانية التعديل والمراجعة الفورية."
        }
    ]

    return (
        <div className="max-w-6xl mx-auto space-y-12 animate-in fade-in duration-700 pb-20">
            {/* Hero Section */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-obsidian-900 to-obsidian-800 border border-gold-500/20 shadow-2xl p-12 text-center">
                <div className="absolute top-0 left-0 w-96 h-96 bg-gold-500/5 rounded-full blur-3xl -ml-40 -mt-20" />
                <div className="absolute bottom-0 right-0 w-96 h-96 bg-cobalt-600/10 rounded-full blur-3xl -mr-40 -mb-20" />

                <div className="relative z-10 space-y-6">
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gold-500/10 border border-gold-500/20 text-gold-400 mb-4"
                    >
                        <Sparkles className="w-4 h-4" />
                        <span>رؤية المستقبل للمحاماة</span>
                    </motion.div>

                    <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent font-cairo leading-tight">
                        مديرك الرقمي الذكي<br />
                        <span className="text-gold-500">لإدارة مكاتب المحاماة</span>
                    </h1>

                    <p className="text-xl text-gray-400 max-w-3xl mx-auto leading-relaxed">
                        ليس مجرد برنامج، بل شريك ذكي يعمل معك. نظام يجمع بين قوة الذكاء الاصطناعي ودقة العمل القانوني<br />
                        لينقل مكتبك نقلة نوعية في الكفاءة والاحترافية.
                    </p>
                </div>
            </div>

            {/* Core Features Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {features.map((feature, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="group p-8 rounded-2xl bg-glass-dark border border-white/5 hover:border-gold-500/30 transition-all duration-300 hover:bg-obsidian-800/50"
                    >
                        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-obsidian-800 to-obsidian-900 border border-white/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 shadow-lg group-hover:shadow-gold-500/10">
                            <feature.icon className="w-7 h-7 text-gold-500" />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-3 group-hover:text-gold-400 transition-colors">
                            {feature.title}
                        </h3>
                        <p className="text-gray-400 leading-relaxed">
                            {feature.description}
                        </p>
                    </motion.div>
                ))}
            </div>

            {/* AI Power Section */}
            <div className="relative rounded-3xl bg-obsidian-800 border border-gray-700 overflow-hidden">
                <div className="grid md:grid-cols-2">
                    <div className="p-12 flex flex-col justify-center space-y-6">
                        <div className="inline-flex items-center gap-2 text-cobalt-400 font-bold tracking-wider uppercase text-sm">
                            <Cpu className="w-4 h-4" />
                            الذكاء الاصطناعي
                        </div>
                        <h2 className="text-3xl font-bold text-white">
                            يعمل لأجلك، يفكر معك
                        </h2>
                        <p className="text-gray-400 text-lg leading-relaxed">
                            باستخدام تقنيات التعلم العميق ومعالجة اللغة الطبيعية، يقوم النظام بفهم سياق قضاياك، واقتراح الإجراءات المناسبة، وتلخيص المستندات المعقدة في ثوانٍ. إنه المساعد الذي لا ينام.
                        </p>
                        <ul className="space-y-4 pt-4">
                            {[
                                "تحليل ذكي للنصوص القانونية والمستندات",
                                "تنبؤ بمواعيد الجلسات وتعارضاتها",
                                "توليد تلقائي للملخصات والتقارير اليومية"
                            ].map((item, i) => (
                                <li key={i} className="flex items-center gap-3 text-gray-300">
                                    <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center">
                                        <Zap className="w-3 h-3 text-green-500" />
                                    </div>
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="relative h-min-96 bg-gradient-to-br from-cobalt-900/50 to-obsidian-900 flex items-center justify-center p-12">
                        {/* Abstract AI Visual */}
                        <div className="relative w-64 h-64">
                            <div className="absolute inset-0 bg-cobalt-500/20 rounded-full animate-pulse blur-3xl" />
                            <div className="relative z-10 w-full h-full bg-glass border border-white/10 rounded-2xl p-6 flex items-center justify-center backdrop-blur-xl transform rotate-3 hover:rotate-0 transition-all duration-500">
                                <Globe className="w-32 h-32 text-cobalt-400 opacity-80" />
                            </div>
                            <div className="absolute -bottom-6 -right-6 w-32 h-32 bg-glass border border-white/10 rounded-xl p-4 flex items-center justify-center backdrop-blur-xl transform -rotate-6 hover:rotate-0 transition-all duration-500 delay-75">
                                <Shield className="w-16 h-16 text-gold-500 opacity-80" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
