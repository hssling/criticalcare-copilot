import { 
  Users, 
  ShieldAlert, 
  ClipboardCheck, 
  ArrowUpRight,
  TrendingUp,
  Activity,
  Zap
} from "lucide-react";
import { motion } from "framer-motion";

export default function Dashboard() {
  const stats = [
    { label: "Active Reviews", value: "12", icon: Users, color: "text-sky-500", bg: "bg-sky-50" },
    { label: "Critical Alerts", value: "3", icon: ShieldAlert, color: "text-rose-500", bg: "bg-rose-50" },
    { label: "Evaluated Today", value: "128", icon: ClipboardCheck, color: "text-emerald-500", bg: "bg-emerald-50" },
    { label: "Model Latency", value: "1.2s", icon: Zap, color: "text-indigo-500", bg: "bg-indigo-50" },
  ];

  return (
    <div className="space-y-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-slate-900">ICU Command Center</h2>
          <p className="text-slate-500">Real-time surveillance and neural clinical decision support.</p>
        </div>
        <div className="flex items-center gap-2 text-sm font-medium text-slate-500 bg-white px-4 py-2 rounded-xl shadow-sm border border-slate-100">
          <Activity size={16} className="text-emerald-500 animate-pulse" />
          Live Telemetry Active
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card p-6 flex items-start justify-between group cursor-default"
          >
            <div className="space-y-1">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{stat.label}</span>
              <div className="text-3xl font-bold text-slate-900">{stat.value}</div>
            </div>
            <div className={`p-3 rounded-xl ${stat.bg} ${stat.color} group-hover:scale-110 transition-transform`}>
              <stat.icon size={24} />
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <section className="glass-card p-8 min-h-[400px] flex flex-col">
             <div className="flex items-center justify-between mb-8">
                <h3 className="text-lg flex items-center gap-2">
                  <TrendingUp size={20} className="text-sky-500" />
                  Cohort Risk Distribution
                </h3>
                <button className="text-xs font-bold text-sky-600 uppercase flex items-center gap-1 hover:underline">
                  Full Analytics <ArrowUpRight size={14} />
                </button>
             </div>
             
             <div className="flex-1 flex items-center justify-center border-2 border-dashed border-slate-100 rounded-2xl bg-slate-50/50 relative overflow-hidden group">
                {/* Decorative Pattern */}
                <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '20px 20px' }} />
                
                <div className="text-center space-y-3 relative z-10 px-6">
                   <div className="mx-auto w-12 h-12 bg-white rounded-full shadow-sm flex items-center justify-center text-slate-300 group-hover:scale-110 transition-transform duration-500">
                     <Activity size={20} />
                   </div>
                   <p className="text-sm font-medium text-slate-400">Telemetry engine ready for data ingestion</p>
                   <p className="text-[10px] text-slate-300 max-w-[200px] mx-auto uppercase tracking-widest font-bold">Mount a clinical cohort to activate visualization</p>
                </div>
             </div>
          </section>
        </div>

        <div className="space-y-6">
           <section className="glass-card p-6 bg-slate-900 text-white min-h-[400px]">
              <h3 className="text-sm border-b border-slate-800 pb-3 mb-6 flex items-center gap-2">
                <ShieldAlert size={16} className="text-rose-400" />
                Urgent Attention
              </h3>
              
              <div className="flex flex-col items-center justify-center h-[280px] text-center space-y-4">
                 <div className="w-12 h-12 bg-slate-800 rounded-full flex items-center justify-center text-slate-500">
                   <ClipboardCheck size={24} />
                 </div>
                 <div className="space-y-1">
                   <p className="text-sm font-medium italic">No critical safety overrides</p>
                   <p className="text-[10px] text-slate-500 uppercase tracking-widest">Safety engine active and surveilling</p>
                 </div>
              </div>
              
              <button className="w-full mt-auto py-3 bg-slate-800 rounded-xl text-xs font-bold uppercase tracking-widest hover:bg-slate-700 transition-colors">
                 Monitor High-Risk Queue
              </button>
           </section>
        </div>
      </div>
    </div>
  );
}
